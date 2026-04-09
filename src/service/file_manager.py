import re
import os
import shutil
import tempfile
from pathlib import Path
import requests
import zipfile

def extract_fits_paths_from_lyric(lyric_path):
    fits_paths = []
    pattern = re.compile(r'^I[a-z][1346]\) \[(.+?\.fits)')

    with open(lyric_path, 'r', encoding='utf-8') as f:
        for line in f:
            match = pattern.match(line.strip())
            if match:
                path = match.group(1)
                if not os.path.isabs(path): # TODO: It should be tested against OSS paths in the future
                    path = os.path.join(os.path.dirname(lyric_path), path)
                fits_paths.append(path)

    return fits_paths

class GalfitsFileManager:
    def __init__(self, prefix="galfits_fitting_"):
        self.prefix       = prefix
        self.pre_hooks = [] 
        self.post_hooks = []
        self.URL          = "https://astro-workbench-bts.lab.zverse.space:32443/api/csst"
        self.DOWNLOAD     = "/fitting/v2/oss/files/download"
        self.CONTENT      = "/fitting/v2/oss/files/content"
        self.UPLOADFILE   = "/fitting/v2/oss/files"
        self.UPLOADFOLDER = "/fitting/v2/oss/folders"

    def __enter__(self):
        self.work_dir = tempfile.mkdtemp(prefix=self.prefix)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, 'work_dir'):
            shutil.rmtree(self.work_dir)

    def download_lyric_and_fits_files(self, lyric_file):
        if not hasattr(self, "work_dir"):
            self.work_dir = tempfile.mkdtemp(prefix=self.prefix)
        local_lyric_file = self.download_file(lyric_file, self.work_dir)    
        fits_files = extract_fits_paths_from_lyric(local_lyric_file)

        for fits_file in fits_files:
            self.download_file(fits_file, os.path.join(self.work_dir, "fits_files"))

        return local_lyric_file, fits_files    

    def copy_lyric_and_fits_files(self, lyric_file):
        # Used for test only as no oss download currently
        if not hasattr(self, "work_dir"):
            self.work_dir = tempfile.mkdtemp(prefix=self.prefix)
        local_lyric_file = os.path.join(self.work_dir, os.path.basename(lyric_file))
        shutil.copy(lyric_file, local_lyric_file)

        fits_files = extract_fits_paths_from_lyric(local_lyric_file)
        for fits_file in fits_files:
            dest_path = os.path.join(self.work_dir, "fits_files", os.path.basename(fits_file))
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copy(fits_file, dest_path)

        return local_lyric_file, fits_files    

    def download_file(self, oss_path, dest_dir="."):
        url = self.URL + self.DOWNLOAD
        os.makedirs(dest_dir, exist_ok=True)

        response = requests.get(url, params={"filePath": oss_path}, stream=True)
        response.raise_for_status()  # 自动抛异常（4xx/5xx）

        is_folder = oss_path.endswith("/")

        if is_folder:
            folder_name = oss_path.strip("/").split("/")[-1] 
            zip_path = os.path.join(dest_dir, f"{folder_name}.zip")
            final_path = os.path.join(dest_dir, folder_name)

            with open(zip_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    f.write(chunk)

            shutil.unpack_archive(zip_path, final_path)
            os.remove(zip_path)
        else:
            file_name = os.path.basename(oss_path)
            final_path = os.path.join(dest_dir, file_name)

            with open(final_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    f.write(chunk)
        return final_path            


    def update_local_lyric_file(self, 
        lyric_file: str,
        *,
        new_img_dir: str=None,
        new_psf_dir: str=None,
        new_sigma_dir: str=None,
        new_mask_dir: str=None
    ):
        config_input_dir = os.path.dirname(lyric_file)
        fits_files_dir = os.path.join(config_input_dir, "fits_files")
        new_img_dir = new_img_dir or fits_files_dir
        new_psf_dir = new_psf_dir or fits_files_dir
        new_sigma_dir = new_sigma_dir or fits_files_dir
        new_mask_dir = new_mask_dir or fits_files_dir

        with open(lyric_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        new_lines = []
        #pattern = re.compile(r'^(I[a-z][1346])\) \[(.+?)([^/]+?\.fits)(.*)\]')
        pattern = re.compile(r'^(I[a-z][1346])\) \[(.+?)([^/]+?\.fits)\s*,\s*([0-9]*)\]')


        for line in lines:
            match = pattern.match(line.strip())
            if not match:
                new_lines.append(line)
                continue

            key = match.group(1)    # 例如 Ia1, Ib3
            prefix = match.group(2) # 旧路径前半部分
            fits_name = match.group(3) # 文件名 f115w.fits
            suffix = match.group(4)   # 后面的 ,0 等

            num = int(re.search(r'\d+', key).group())
            if num not in {1, 3, 4, 6}:
                new_lines.append(line)
                continue

            if num == 1:
                new_path = Path(new_img_dir) / fits_name
            elif num == 3:
                new_path = Path(new_sigma_dir) / fits_name
            elif num == 4:
                new_path = Path(new_psf_dir) / fits_name
            else:
                new_path = Path(new_mask_dir) / fits_name

            new_line = f"{key}) [{new_path},{suffix}]\n"
            new_lines.append(new_line)

        with open(lyric_file, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
    
    def add_pre_hook(self, callable_func, **kwargs):
        self.pre_hooks.append({"func": callable_func, "args": kwargs})

    def add_post_hook(self, callable_func, **kwargs):
        self.post_hooks.append({"func": callable_func, "args": kwargs})

    def upload_file(self, local_file_path, oss_file_path):
        url = self.URL + self.UPLOADFILE

        with open(local_file_path, "rb") as f:
            files = {"file": (os.path.basename(local_file_path), f)}
            data = {"filePath": oss_file_path}
            resp = requests.post(url, files=files, data=data)

        resp.raise_for_status()

    def upload_folder(self, local_folder_path, target_path):
        if not target_path.endswith("/"):
            target_path += "/"

        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_zip:
            zip_filename = temp_zip.name

        with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(local_folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, local_folder_path)
                    zipf.write(file_path, rel_path)

        url = self.URL + self.UPLOADFOLDER

        with open(zip_filename, "rb") as f:
            files = {"file": f}
            data = {"targetPath": target_path}
            resp = requests.post(url, files=files, data=data)

        resp.raise_for_status()
        os.unlink(zip_filename)

    def run_pre_hooks(self):
        for hook in self.pre_hooks:
            hook["func"](**hook["args"])
    
    def run_post_hooks(self):
        for hook in self.post_hooks:
            hook["func"](**hook["args"])        
            
def TEST_extract_fits_paths():
    lyric_path = "/home/jiangbo/galaxy_morphology_mcp/GALFITS_examples/40/obj40_s2_sed_opt_free.lyric"
    fits_paths = extract_fits_paths_from_lyric(lyric_path)
    for path in fits_paths:
        print(path)

if __name__ == "__main__":
    # TEST_extract_fits_paths()
    with GalfitsFileManager() as fm:
        lyric_file = "/home/jiangbo/GALFITS_examples/latest/configs/obj692"
        fm.add_pre_hook(fm.copy_lyric_and_fits_files, lyric_file=lyric_file)
        fm.add_pre_hook(fm.update_local_lyric_file, lyric_file=os.path.join(fm.work_dir, os.path.basename(lyric_file)))
        fm.run_pre_hooks()
        print("Pre-hooks executed. Local files prepared at:", fm.work_dir)

        import sys        
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        from tools.galfits_fitting import ImageFitting, PureSEDFitting, ImageSEDFitting

        result = ImageFitting(lyric_file=os.path.join(fm.work_dir, os.path.basename(lyric_file)), workplace=os.path.join(fm.work_dir, "result"), args=[])
        print("Fitting result:", result)

        result = PureSEDFitting(lyric_file=os.path.join(fm.work_dir, os.path.basename(lyric_file)), new_lyric_file=os.path.join(fm.work_dir,os.path.basename(lyric_file)), workplace=os.path.join(fm.work_dir, "result"), args=[])
        print("Fitting result:", result)

        result = ImageSEDFitting(lyric_file=os.path.join(fm.work_dir, os.path.basename(lyric_file)), workplace=os.path.join(fm.work_dir, "result_is"), args=[])
        print("Fitting result:", result)

        fm.run_post_hooks()
        
        
