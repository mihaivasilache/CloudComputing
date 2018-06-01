from azure.storage.file import FileService, ContentSettings
import time

fileService = FileService(account_name='cs7b04dc31e3552x4267x9c3', account_key='ihwu6KLKRkUv3/dF3ELyhqbsB34jUJGyyVexD3gr2PUhcL3X5XFg/aFumVEHZCUHqqfP+m2UBM1Lni3uw26WcA==')
filesDir = 'fileshare'
#fileService.create_share(filesDir)

def getFiles(dirName):
    files = []
    try:
        generator = fileService.list_directories_and_files(filesDir, dirName)
        for file_or_dir in generator:
            files.append({'name': file_or_dir.name, 'length': file_or_dir.properties.content_length})
    except Exception as e:
        print(e)
        files = []
    return files

def getFile(dirName, fileName):
    file_ = fileService.get_file_to_text(filesDir, dirName, fileName)
    return file_

def createDir(dirName):
    fileService.create_directory(filesDir, dirName)
    
def saveFile(fileName, fileText, dirName):
    fileService.create_file_from_text(filesDir, dirName, fileName, fileText, content_settings=ContentSettings())

#print(getFiles('test'))