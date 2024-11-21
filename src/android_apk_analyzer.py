import zipfile
import json

class CcuApkAnalyzer:
    
    def __init__(self, apk_path):
        self.apk_path = apk_path
        self.model_directory_path = "assets/assets/75f/models/"
        self.version_json_path = "assets/assets/75f/versions.json"
        try:
            self.apk_zip = zipfile.ZipFile(apk_path, 'r')
        except zipfile.BadZipFile:
            print("Bad zip file")
            self.apk_zip = None

    def check_mandatory_items(self):
        print(f"Checking mandatory items from {self.apk_zip.filename}")
        mandatory_items = [self.model_directory_path, self.version_json_path]
        all_items_found = 0
        
        n = 0
        for mandatory_item in mandatory_items:
            item_found = False
            for extracted_item in self.apk_zip.namelist():
                n += 1
                if extracted_item.startswith(mandatory_item):
                    item_found = True
                    all_items_found += 1
                    break
            print(f"\t{mandatory_item} found: {item_found}")
            print(f"\t\tattempts for {mandatory_item}: {n}")
            n = 0
        return all_items_found == 2
    
    def fetch_valid_json(self, myjson):
        try:
            with self.apk_zip.open(myjson) as json_read:
                json_object = json.load(json_read)
        except ValueError as e:
            return False, None
        return True, json_object
            
    def fetch_versions_data(self):
        is_versions_valid, version_json = self.fetch_valid_json(self.version_json_path)
        model_id_dict = {}
        if is_versions_valid:
            for mode_item in version_json.values():
                model_id_dict[mode_item["id"]] = str(mode_item["version"]["major"]) + "." + str(mode_item["version"]["minor"]) + "." + str(mode_item["version"]["patch"])      
            return True, model_id_dict
        else:
            print("Versions json is not valid")
            return False, None

    def find_in_use_model_files(self, model_id_dict):
        print("Finding in use model files")
        model_files_not_found = []
        for model_id in model_id_dict.keys():
            model_path = self.model_directory_path + model_id + ".json"
            if model_path not in self.apk_zip.namelist():
                model_files_not_found.append(model_id)
                print(f"Model id {model_id} not found")
        if len(model_files_not_found) > 0:
            return False, model_files_not_found
        else:
            print("\tAll model files found")
            return True, None

    def validate_in_use_model_files(self, model_id_dict):
        continue_validation = True
        print("Validating in use model files")
        for model_id in model_id_dict.keys():
            model_file_path = self.model_directory_path + model_id + ".json"
            is_valid, model_file_json = self.fetch_valid_json(model_file_path)
            if not is_valid:
                print(f"\tModel file not valid: {model_id}")
                continue_validation = False
        if continue_validation == True:
            print("\tAll model files are valid")
        return continue_validation
    
    def fetch_in_use_model_files(self, model_id_dict):
        print("Fetching in use model files")
        model_files = {}
        for model_id in model_id_dict.keys():
            model_file_path = self.model_directory_path + model_id + ".json"
            with self.apk_zip.open(model_file_path) as model_file:
                model_files[model_id] = json.load(model_file)
        return model_files
    
    def get_info(self, model_id_dict):
        print(f"Getting model file size info for {self.apk_zip.filename}")
        model_size_dict = {}
        for model_id in model_id_dict.keys():
            model_file_path = self.model_directory_path + model_id + ".json"
            model_file_info = self.apk_zip.getinfo(model_file_path)
            model_size_dict[model_id] = model_file_info.file_size   
        return model_size_dict             