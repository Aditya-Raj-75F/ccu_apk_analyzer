from android_apk_analyzer import CcuApkAnalyzer

import argparse
import os

global parser
parser = None

def initParser():
    global parser
    parser = argparse.ArgumentParser(description="CCU APK Analyzer")

    # Add an argument to specify the source of input
    parser.add_argument("-s", "--source", type=str, choices=["file", "folder"], default="folder",
                        help="Specify the source of input: 'file' for single apk input, 'folder' for all apks in a folder")

    # Add an argument to clarify whether the apk comparison with old apk is required
    parser.add_argument("-c", "--compare", type=str, choices=["y", "n"], default="n",
                        help="Specify whether the apk comparison with old apk is required: 'y' for yes, 'n' for no")

    # Add an argument to specify whether the model change is expected
    parser.add_argument("-m", "--model_change", type=str, choices=["y", "n"], default="n",
                        help="Specify whether the model change is expected: 'y' for yes, 'n' for no")

    # Add an argument supporting source of input to specify the source path especially if source of input is file
    parser.add_argument("-p", "--pathname", type=str, default=None,
                        help="Specify the input source path")
    
    # Add an argument supporting source of old apk file to compare with the new apk or apks
    parser.add_argument("-o", "--old_apk", type=str, default=None,
                        help="Specify the old apk file path to compare with the new apk or apks")

def list_ccu_apk_files_directory(directory_path):
    return [file for file in os.listdir(directory_path) if ".apk" in file]

def analyse_indiviual_apk(apk_file_path):
    print("\nAnalyzing apk file: ", apk_file_path)
    ccu_apk_analyser = CcuApkAnalyzer(apk_file_path)
        
    if ccu_apk_analyser.check_mandatory_items() == False:
        print("Mandatory items not found in the apk file")
        return False, None
        
    is_valid, model_id_dict = ccu_apk_analyser.fetch_versions_data()
    print(f"Total models in use: {len(model_id_dict)}")
    if is_valid == False:
        print("Versions json is not valid")
        return False, None
        
    all_models_found, models_not_found_list = ccu_apk_analyser.find_in_use_model_files(model_id_dict)
    if all_models_found == False:
        print(f"Model files not found for model ids: {models_not_found_list}")
        return False, None
        
    if ccu_apk_analyser.validate_in_use_model_files(model_id_dict) == False:
        print("Model files are not valid")
        return False, None
    
    return True, model_id_dict
    
def identify_model_version_updates(new_model_id_dict, old_model_id_dict):
    version_change_found = False
    for model_id, new_version in new_model_id_dict.items():
        if model_id in old_model_id_dict.keys():
            old_version = old_model_id_dict[model_id]
            if new_version != old_version:
                print(f"Model version mismatch found for model id {model_id}, new version: {new_version}, old version: {old_version}")
                version_change_found = True
        else:
            print(f"Model id: {model_id} not found in old apk")
            version_change_found = True
    for model_id, old_version in old_model_id_dict.items():
        if model_id not in new_model_id_dict.keys():
            print(f"Model id: {model_id} not found in new apk")
            version_change_found = True
    return version_change_found
    
def compare_model_sizes(new_model_sizes, old_model_sizes):
    model_changes_found = False
    for model_id, new_model_size in new_model_sizes.items():
        if model_id in old_model_sizes.keys():
            old_model_size = old_model_sizes[model_id]
            if new_model_size != old_model_size:
                model_changes_found = True
                print(f"Model size mismatch found for model id {model_id}, new size: {new_model_size}, old size: {old_model_size}")
        else:
            model_changes_found = True
            print(f"Model id: {model_id} not found in old apk")
    for model_id, old_model_size in old_model_sizes.items():
        if model_id not in new_model_sizes.keys():
            model_changes_found = True
            print(f"Model id: {model_id} not found in new apk")
    return model_changes_found

def compare_with_old_apk(new_model_id_dict, old_apk_file_path, new_apk_file_path, is_model_change_expected):
    print(f"\nComparing new apk: {new_apk_file_path} with old apk: {old_apk_file_path}")
    ccu_old_apk_analyser = CcuApkAnalyzer(old_apk_file_path)
            
    is_valid, old_model_id_dict = ccu_old_apk_analyser.fetch_versions_data()
    if is_valid == False:
        print("Versions json is not valid")
        return False
    else:
        print(f"Total models in use in old apk: {len(old_model_id_dict)}")
        
    version_change_detected = identify_model_version_updates(new_model_id_dict, old_model_id_dict)
    if is_model_change_expected == "y" and version_change_detected == False:
        print("Model version change expected but not found. Please rebuild the apk")
        return False
    if is_model_change_expected == "n" and version_change_detected == True:
        print("Model version change not expected but found. Please rebuild the apk")
        return False
    if is_model_change_expected == "y" and version_change_detected == True:
        print("Model version change expected and found. Skipping model size comparison")
        return True
    
    print("Model version change not expected and not found. Proceeding with model size comparison")
    ccu_new_apk_analyser = CcuApkAnalyzer(new_apk_file_path)
    new_model_size_dict = ccu_new_apk_analyser.get_info(new_model_id_dict)
    old_model_size_dict = ccu_old_apk_analyser.get_info(old_model_id_dict)
    model_changes_found = compare_model_sizes(new_model_size_dict, old_model_size_dict)   
    if model_changes_found == True:
        print("Model size mismatch found. Please rebuild the apk.")
        return False
    else:
        print("Model size matched.")
        return True 
    
def perform_complete_validation(apk_file_path, old_apk_file_path, args):
    individual_validation, model_id_dict = analyse_indiviual_apk(apk_file_path)
    if individual_validation == True and args.compare == "y" and old_apk_file_path is not None:
        print(f"\nApk file path: {apk_file_path} contains the assets/assets/models and versions.json and all in-use models are syntactically correct.")
        if compare_with_old_apk(model_id_dict, old_apk_file_path, apk_file_path, args.model_change):
            print(f"\nApk file {apk_file_path} seems to have valid model changes if any.")
        else:
            print(f"\nApk file {apk_file_path} does not have valid models as per comparison with older apk.")
    

if __name__ == "__main__":
    
    initParser()
    
    args = parser.parse_args()
    print(args)
    
    old_apk_file_path = None
    
    if args.compare == "y" and not args.old_apk:
        parser.error("Please specify the old apk file path to compare with the new apk or apks")
        exit()
    elif args.compare == "y":
        old_apk_file_path = args.old_apk
    
    if args.source == "folder":
        sourcePath = "."
        if args.pathname is not None:
            print("pathname specified for folder")
            sourcePath = args.pathname
        all_apk_files = list_ccu_apk_files_directory(sourcePath)
        for apk_file in all_apk_files:
            apk_file_path = os.path.join(sourcePath, apk_file)
            perform_complete_validation(apk_file_path, old_apk_file_path, args)
    elif args.source == "file" and not args.pathname:
        parser.error("Please specify the pathname for the apk file when source is --file")
        exit()
    else:
        apk_file_path = args.pathname
        perform_complete_validation(apk_file_path, old_apk_file_path, args)
        