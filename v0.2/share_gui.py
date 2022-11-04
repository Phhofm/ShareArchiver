"""
v0.2
Share Archiver - Python File
Made by Philip Hofmann as a personal / hobby project to play around.
Optimizing for file sharing by reducing archive size and still having fast decompression speeds. Therefore choosing strong asymmetric compression algorithms.
The underlying assumption is, that each file has an optimal archiver concerning minimal compression size and decompression speeds, and compressing each file separately and adding it to a mixed archive achieves better results.
This might work well with large files, but worse with very small files, since each compressor adds a header to each compressed file, which might result in a larger archive than directory size, but only in this special usecase.
We therefore compress each file with each compressor and only use the smallest file and add it to the archive. Since strong asymmetric compressors are chosen, this results in long compression times but fast decompression speeds with small archive size.

This is a Linux only application so far, development takes place on Ubuntu 20.04.4 LTS focal
"""

import PySimpleGUI as sg
import tarfile
import zlib
import tempfile
import shutil
import glob
import tarfile
import bz2
import lzma
import os
import gzip
import zstd
import pyppmd  # beta
import lz4.frame
import brotli
import lzham
from zopfli.zlib import compress
import sys  # only for developing, with sys.exit() i can break execution without commenting the rest
from distutils.dir_util import copy_tree
import time  # measuring application execution time
import enum  # to be honest, i am not exactly sure if i needed to incorporate enums, first i thought it would be cleaner and less error-prone to inclue integer levels instead of strings for example, but could just have worked with integers the whole code
import multiprocessing  # to start compressors simultaneously for faster compression
import signal
from termcolor import colored  # giving colored output
import json  # for adjusting the info.json file and include it in the archive. This will help with debugging, im storing system information of the compressing system. For decompressing, i can read it out and show the user that he tried to decompress on another platform for example. Or which version it was compressed with. Show in output that newer versions might include more compressors, so decompressing archives that have been created by a newer version might not work.
import platform  # to append system info of the compressor system to the info.json
import subprocess  # for external binary calls (the compressors)

# file extensions of used compressors (used both in compresssion and decompression action sections)
extension0 = ".zlib"
extension1 = ".bz2"
extension2 = ".xz"
extension3 = ".gz"
extension4 = ".zst"
extension5 = ".ppmd"
extension6 = ".lz4"
extension7 = ".brotli"
extension8 = ".lzham"
extension9 = ".zopfli"
extension10 = ".lzt"
extension11 = ".glza"
extension12 = ".balz"
extension13 = ".bsc"
extension14 = ".csa"
extension15 = ".nncp"
extension16 = ".zpaq"


def COMPRESS(inputDir, outputDir, compressionLvl, memorySaverLvl):
    # the version. Important because later on, there might be windows only versions. Or if one has more compressors and decompressors, they will be able to decompress old share versions, but old share versions might not be able to decompress archives of newer versions.
    print(colored("Share Archiver Version 0.1 by Philip Hofmann", "green"))
    print("This is a Linux application, tested and developed on Ubuntu 20.04.3 LTS")
    print("Starting compression")
    print("Compressing " + inputDir)
    print("Compressing to " + outputDir)
    print("Compression Level set to " + compressionLvl)
    print("Memory Saver set to " + memorySaverLvl)
    verbose = False
    # this gets appended to the console commands to execute the external executables as to suppress output for clean output. If -v is chosen, this actually gets replaced with "" so nothing is appended to the execution commands of the external files so they will print outputs to the console.
    supressOutputAppend = " >/dev/null 2>&1"
    # this simply will be the sum of all the original uncompressed files in the input folder. Meaning the overall size of the input folder, so we can compare and calculate and outprint the compression ratio at the end (compare with archive size)
    folderSize = 0

    verbose = False
    # supressOutputAppend = ""

    # TODO rename all output_path instances to outputDir. Ill leave it to copy code for now
    output_path = outputDir
    input_path = inputDir

    archiveName = os.path.basename(inputDir)

    print("Start process to create " + archiveName + ".share")

    # TODO rewrite for python to manage the temporary folder itself not by you manually creating folders and deleting them
    # delete sharetmp folder if still exists from for example manually interrupted compression with Ctrl+C previously.
    if os.path.exists(os.getcwd() + "/sharetmp"):
        shutil.rmtree(os.getcwd() + "/sharetmp")

    # if interruption, clean up tmp folder

    def signal_handle(_signal, frame):
        print("Interruption. Stopping the Jobs and cleaning up. Please wait ...")
        if os.path.exists(os.getcwd() + "/sharetmp"):
            shutil.rmtree(os.getcwd() + "/sharetmp")

    signal.signal(signal.SIGINT, signal_handle)

    # timer, start tracking time for output
    start_time = time.time()  # for monitoring execution time

    # enums for compression level TODO refactor enums not needed anymore since gui values

    class CompressionLevel(enum.Enum):
        Fast = "Fast"
        # leave all compressors with default setting (no changes in arguments)
        Default = "Default"
        # TODO finetune settings?use stronger compression that still gives fast decompression like level 39 for lzturbo according to its own benchmark
        Optimized = "Optimized"
        # I just want max compression. # TODO insert ZPAQ, PAQ8pxd, with precomp, just look at matt mahoneys benchmarks and choose the most powerful in this profile, speeds do not matter (time=unlimited)
        Strongest = "Strong"  # just max setting for each asymmetric compressor
        # add strong compressors with strongest settings like nccp, zpaq, paq8pxd, fp8 ...
        Max = "Max"
        # Insane = "Insane"

    # for pyinstaller single executable file
    # get the path to the temporary folder created by pyinstaller

    def resource_path(relative_path):
        """Get absolute path to resource, works for dev and for PyInstaller"""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    # set compression level
    if compressionLvl == "Fast":
        print(colored("Fast Compression Profile", "cyan"))
        compression = CompressionLevel.Fast
        print("Compressors used: xz, bsc and csa with default compression settings")
    elif compressionLvl == "Default":
        print(colored("Default Compression Profile", "cyan"))
        compression = CompressionLevel.Default
        print(
            "Compressors used: zlib, bz2, xz, gz, zst, ppmd, lz4, brotli, lzham, zopfli, lzt, glza, balz, bsc and csa with default compression settings"
        )
    elif compressionLvl == "Strong":
        print(colored("Strong Compression Profile", "cyan"))
        compression = CompressionLevel.Strongest
        print(
            "Compressors used: zlib, bz2, xz, gz, zst, ppmd, lz4, brotli, lzham, zopfli, lzt, glza, balz, bsc and csa with strongest compression method"
        )
    elif compressionLvl == "MAX":
        print(colored("MAX Compression Profile", "red"))
        compression = CompressionLevel.Max
        print(
            "Compressors used: zlib, bz2, xz, gz, zst, ppmd, lz4, brotli, lzham, zopfli, lzt, glza, balz, bsc, csa, nncp and zpaq with strongest compression method"
        )
        print(
            colored(
                "Warning: Do not use level 3 for online file distribution as this level will frustrate downloaders with long decompression times.",
                "yellow",
            )
        )
        print("Compressing now ... this will take a while")
    else:
        compression = CompressionLevel.Default
        print(
            "Compressors used: zlib, bz2, xz, gz, zst, ppmd, lz4, brotli, lzham, zopfli, lzt, glza, balz, bsc and csa with default compression settings"
        )

    # Default Profile, asymmetric compressors enabled
    compressor0 = True
    compressor1 = True
    compressor2 = True
    compressor3 = True
    compressor4 = True
    compressor5 = True
    compressor6 = True
    compressor7 = True
    compressor8 = True
    compressor9 = True
    compressor10 = True
    compressor11 = True
    compressor12 = True
    compressor13 = True
    compressor14 = True
    compressor15 = False
    compressor16 = False

    # Fast level. Uses only xz, bsc and csa compressors. Using default compressor settings.
    if compression == CompressionLevel.Fast:
        compressor0 = False
        compressor1 = False
        compressor3 = False
        compressor4 = False
        compressor5 = False
        compressor6 = False
        compressor7 = False
        compressor8 = False
        compressor9 = False
        compressor10 = False
        compressor11 = False
        compressor12 = False
        compressor15 = False
        compressor16 = False

    # Max Level. Additionally enable symmetric compressors
    if compression == CompressionLevel.Max:
        compressor15 = True
        compressor16 = True

    # initialize original filepaths compressor arrays - be basically store the original filepaths per compressor, so we will be able to recompress all together in one swoop with that compressor, this might help with inter-file redundancies.
    compressor0OriginalsArray = []
    compressor1OriginalsArray = []
    compressor2OriginalsArray = []
    compressor3OriginalsArray = []
    compressor4OriginalsArray = []
    compressor5OriginalsArray = []
    compressor6OriginalsArray = []
    compressor7OriginalsArray = []
    compressor8OriginalsArray = []
    compressor9OriginalsArray = []
    compressor10OriginalsArray = []
    compressor11OriginalsArray = []
    compressor12OriginalsArray = []
    compressor13OriginalsArray = []
    compressor14OriginalsArray = []
    compressor15OriginalsArray = []
    compressor16OriginalsArray = []

    # the same thing again, but with the already compressed filepaths. If the array stays empty, this compressor has not been used for any of the files. If there is only 1 file in it, we can just delete that file in the corresponding original filepaths compressor array. If there are multiple, we delete the files from this array (since they have been compressed singily) and compress the original files in one swoop with the same compressor. These compressors handle inter-file redundancies by themselves I think.
    compressor0CompressedArray = []
    compressor1CompressedArray = []
    compressor2CompressedArray = []
    compressor3CompressedArray = []
    compressor4CompressedArray = []
    compressor5CompressedArray = []
    compressor6CompressedArray = []
    compressor7CompressedArray = []
    compressor8CompressedArray = []
    compressor9CompressedArray = []
    compressor10CompressedArray = []
    compressor11CompressedArray = []
    compressor12CompressedArray = []
    compressor13CompressedArray = []
    compressor14CompressedArray = []
    compressor15CompressedArray = []
    compressor16CompressedArray = []

    # create copy folder, copy files
    createFolder = os.getcwd() + "/sharetmp"

    try:
        os.mkdir(createFolder)
    except OSError:
        # fore example directory exists already
        if verbose:
            print("Creation of copy directory failed")
    else:
        if verbose:
            print("Successfully created copy directory ")

    # copy all input files into that copy folder and keep folder structure
    if verbose:
        print("Making copies of original files")
    copy_tree(input_path, createFolder)
    if verbose:
        print("Copied all files for compression")

    # PRECOMP SECTION - Preprocessing every single file in this folder with precomp, which gives a .pcf file (but we preserve original extension)
    # Do not forget to run precomp again after compressing files into folder to restore original files

    print("Precompressing Files with Precomp")

    # we want the file to be better compressable. We preserve the file extension so we can restore the file later to a specific path.
    def precompress(filepath):
        try:
            subprocess.run(
                resource_path("")
                + "precomp -cn -intense -e "
                + filepath,
                shell=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except:
            print("Could not precompress")

    # we remove the original copied files to the sharetmp folder
    def removeunpreprocessed(filepath):
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
            else:
                print("The unpreprocessed file " +
                      filepath + " does not exist")
        except:
            print("Could not remove unpreprocessed file " + filepath)

    # need to iterate all files to find the total number of files to precompress for the console output. We cannot use len(files) since this will only show us how many files are in the current subfoler (or in other words, if all files are in the same folder and no subfolders are present, then it would give the same integer, but not otherwise)
    totalNumberOfFiles = 0
    for subdir, dirs, files in os.walk(createFolder):
        for filename in files:
            totalNumberOfFiles = totalNumberOfFiles + 1

    # variable for console output, for "File 3 of 15"
    fileprocesscounter = 0
    # for each file in temporary folder with all copied files (os.walk to iterate over all descendant files in subdirectories)
    for subdir, dirs, files in os.walk(createFolder):
        for filename in files:
            # update filecounter
            fileprocesscounter = fileprocesscounter + 1
            print(
                "Precompressing File "
                + str(fileprocesscounter)
                + " of "
                + str(totalNumberOfFiles)
            )
            # variables
            filepath = str(subdir + os.sep + filename)
            filesizeoriginal = os.stat(filepath).st_size
            # we sum up foldersize so at the end we know how big the input folder was and can compare it with the archive for compression ratio calculation
            folderSize = folderSize + filesizeoriginal
            # precompress each file in sharetmp and remove original
            precompress(filepath)
            removeunpreprocessed(filepath)

    # END OF PRECOMP

    # SREP SECTION - Further preprocessing files with srep after precomp

    # print("Further Precompressing Files with SREP")

    # # we want the file to be better compressable. We preserve the file extension so we can restore the file later to a specific path.
    # def srep(filepath):
    #     try:
    #         subprocess.run(
    #             resource_path("")
    #             + "srep64 "
    #             + filepath,
    #             shell=True,
    #             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    #         )
    #     except:
    #         print("Could not further precompress")

    # # we remove the original pcf copied files to the sharetmp folder
    # def removepreprocessed(filepath):
    #     try:
    #         if os.path.exists(filepath):
    #             os.remove(filepath)
    #         else:
    #             print("The preprocessed file " +
    #                   filepath + " does not exist")
    #     except:
    #         print("Could not remove preprocessed file " + filepath)

    # # need to iterate all files to find the total number of files to precompress for the console output. We cannot use len(files) since this will only show us how many files are in the current subfoler (or in other words, if all files are in the same folder and no subfolders are present, then it would give the same integer, but not otherwise)
    # totalNumberOfFiles = 0
    # for subdir, dirs, files in os.walk(createFolder):
    #     for filename in files:
    #         totalNumberOfFiles = totalNumberOfFiles + 1

    # # variable for console output, for "File 3 of 15"
    # fileprocesscounter = 0
    # # for each file in temporary folder with all copied files (os.walk to iterate over all descendant files in subdirectories)
    # for subdir, dirs, files in os.walk(createFolder):
    #     for filename in files:
    #         # update filecounter
    #         fileprocesscounter = fileprocesscounter + 1
    #         print(
    #             "SREP-ing File "
    #             + str(fileprocesscounter)
    #             + " of "
    #             + str(totalNumberOfFiles)
    #         )
    #         # variables
    #         filepath = str(subdir + os.sep + filename)
    #         filesizeoriginal = os.stat(filepath).st_size
    #         # we sum up foldersize so at the end we know how big the input folder was and can compare it with the archive for compression ratio calculation
    #         #folderSize = folderSize + filesizeoriginal
    #         # precompress each file in sharetmp and remove original
    #         srep(filepath)
    #         removepreprocessed(filepath)

    # END OF SREP

    # COMPRESSOR COMMANDS
    # all the compression methods here, with their settings for the profiles

    # zlib values: 0 - 9

    def zlibcompress(filename, filepath, directory):
        if verbose:
            print("Multicompress zlb")
        with open(filepath, mode="rb") as fin, open(
            directory + "/" + filename + extension0, mode="wb"
        ) as fout:
            data = fin.read()
            if compression == CompressionLevel.Strongest:
                compressed_data = zlib.compress(
                    data, zlib.Z_BEST_COMPRESSION
                )  # level 9
            elif compression == CompressionLevel.Optimized:
                compressed_data = zlib.compress(
                    data, zlib.Z_DEFAULT_COMPRESSION
                )  # level 6
            else:
                compressed_data = zlib.compress(
                    data, zlib.Z_DEFAULT_COMPRESSION
                )  # level 6
            if verbose:
                print(
                    f"zlib Compressed size: {sys.getsizeof(compressed_data)}")
            fout.write(compressed_data)

    # bz2  compresslevel=9 is strongest and default at the same time so we do not need to differentiate at all here. values 0 - 9
    def bz2compress(filename, filepath, directory):
        if verbose:
            print("Multicompress bz2")
        with open(filepath, mode="rb") as fin, bz2.open(
            directory + "/" + filename + extension1, "wb", compresslevel=9
        ) as fout:
            fout.write(fin.read())
            if verbose:
                print(
                    f"bz2 Compressed size: {os.stat(directory +'/'+filename+extension1).st_size}"
                )

    # lzma/xz values: 0 - 9
    def lzmacompress(filename, filepath, directory):
        if verbose:
            print("Multicompress lzma")
        if compression == CompressionLevel.Strongest:
            lzc = lzma.LZMACompressor(preset=9)
        else:
            # default and optimized in this case is level 6 or PRESET_DEFAULT.
            lzc = lzma.LZMACompressor(preset=6)
        with open(filepath, mode="rb") as fin, open(
            directory + "/" + filename + extension2, "wb"
        ) as fout:
            data = fin.read()
            compressed_data = lzma.compress(data)
            if verbose:
                print(
                    f"lzma/xz Compressed size: {sys.getsizeof(compressed_data)}")
            fout.write(compressed_data)

    # gzip compresslevel=9 is strongest and default at the same time so we do not need to differentiate at all here. values: 0 - 9
    def gzipcompress(filename, filepath, directory):
        if verbose:
            print("Multicompress glza")
        with open(filepath, "rb") as fin, gzip.open(
            directory + "/" + filename + extension3, "wb"
        ) as fout:
            # Reads the file by chunks to avoid exhausting memory
            shutil.copyfileobj(fin, fout)
            if verbose:
                print(
                    f"gzip Compressed size: {os.stat(directory +'/'+filename+extension3).st_size}"
                )

    # zstd values: ultra-fast levels from -100 (ultra) to -1 (fast) available since zstd-1.3.4, and from 1 (fast) to 22 (slowest), 0 or unset - means default (3). Default - 3
    def zstdcompress(filename, filepath, directory):
        if verbose:
            print("Multicompress zstd")
        with open(filepath, mode="rb") as fin, open(
            directory + "/" + filename + extension4, "wb"
        ) as fout:
            data = fin.read()
            if compression == CompressionLevel.Strongest:
                compressed_data = zstd.compress(data, 22)
            else:
                compressed_data = zstd.compress(data)  # default is -3
            if verbose:
                print(
                    f"zstd Compressed size: {sys.getsizeof(compressed_data)}")
            fout.write(compressed_data)

    # ppmd (beta) values: up to 12 (no errors) not documented well enough therefore manual trial and error. Over max order 12 it gives vorrupted input data errors when decompressing.
    def ppmdcompress(filename, filepath, directory):
        if verbose:
            print("Multicompress ppmd")
        with open(filepath, mode="rb") as fin, open(
            directory + "/" + filename + extension5, "wb"
        ) as fout:
            data = fin.read()
            if compression == CompressionLevel.Strongest:
                compressed_data = pyppmd.compress(data, max_order=12)
            else:
                compressed_data = pyppmd.compress(data)
            if verbose:
                print(
                    f"ppmd Compressed size: {sys.getsizeof(compressed_data)}")
            fout.write(compressed_data)

    # lz4 values: 0-16, default 0
    def lz4compress(filename, filepath, directory):
        if verbose:
            print("Multicompress lz4")
        with open(filepath, mode="rb") as fin, open(
            directory + "/" + filename + extension6, "wb"
        ) as fout:
            data = fin.read()
            if compression == CompressionLevel.Strongest:
                compressed_data = lz4.frame.compress(
                    data, compression_level=16)
            else:
                compressed_data = lz4.frame.compress(data)
            if verbose:
                print(
                    f"lz4 Compressed size: {sys.getsizeof(compressed_data)}")
            fout.write(compressed_data)

    # brotli values 1-11
    def brotlicompress(filename, filepath, directory):
        if verbose:
            print("Multicompress brotli")
        with open(filepath, mode="rb") as fin, open(
            directory + "/" + filename + extension7, "wb"
        ) as fout:
            data = fin.read()
            if compression == CompressionLevel.Strongest:
                compressed_data = brotli.compress(data, quality=11)
            else:
                # see 'fast.txt' file for how i chose this default vaule. beforehand I just did not pass any quality argument, but then recognized that it chose level 11 as default, which took way too long in the benchmark for the fast profile
                compressed_data = brotli.compress(data, quality=9)
            if verbose:
                print(
                    f"brotli Compressed size: {sys.getsizeof(compressed_data)}")
            fout.write(compressed_data)

    # lzham values 1-4
    # what I am doing here: to decompress, we need to give as an argument/header the uncompressed file size. Normally this is stored in the lzham header, but the dev of this library did not know about it/indluce it.
    # there is a pull request pending with integrating header but has not been merged
    # this is why i store this information in the filename, and extract it from the filename to decompress. of course, for the end user, this will be cleaned up when decompressing
    def lzhamcompress(filename, filepath, directory):
        if verbose:
            print("Multicompress lzham")
        with open(filepath, mode="rb") as fin, open(
            directory
            + "/"
            + filename
            + "__"
            + str(os.path.getsize(filepath))
            + extension8,
            "wb",
        ) as fout:
            data = fin.read()
            if compression == CompressionLevel.Strongest:
                filters = {"level": 4}
                compressed_data = lzham.compress(data, filters)
            else:
                compressed_data = lzham.compress(data)
            if verbose:
                print(
                    f"lzham Compressed size: {sys.getsizeof(compressed_data)}")
                print(os.path.getsize(filepath))
            fout.write(compressed_data)

    # zopfli
    def zopflicompress(filename, filepath, directory):
        if verbose:
            print("Multicompress zopfli")
        with open(filepath, mode="rb") as fin, open(
            directory + "/" + filename + extension9, "wb"
        ) as fout:
            data = fin.read()
            if compression == CompressionLevel.Strongest:
                compressed_data = compress(
                    data, numiterations=25)  # 25 seems good
            else:
                compressed_data = compress(data)
            if verbose:
                print(
                    f"zopfli Compressed size: {sys.getsizeof(compressed_data)}")
            fout.write(compressed_data)

    # external binaries, included with pyinstaller

    # lzturbo
    def lzturbocompress(filepath, directory):
        if verbose:
            print("Multicompress lzturbo")
            if compression == CompressionLevel.Strongest:
                try:
                    subprocess.run(
                        resource_path("") + "lzturbo -49 " +
                        filepath + " " + directory,
                        shell=True,
                    )
                except:
                    print("Could not run compressor lzturbo")
            else:  # at its own benchmark site: decomp speeds of 1622.37 still with 39. and there is no default i think. when using 49 it drops drastically to 57.81
                try:
                    subprocess.run(
                        resource_path("") + "lzturbo -39 " +
                        filepath + " " + directory,
                        shell=True,
                    )
                except:
                    print("Could not run compressor lzturbo")
        else:
            if compression == CompressionLevel.Strongest:
                try:
                    subprocess.run(
                        resource_path("") + "lzturbo -49 " +
                        filepath + " " + directory,
                        shell=True,
                        capture_output=True,
                        text=True,
                    )
                except:
                    print("Could not run compressor lzturbo")
            else:  # at its own benchmark site: decomp speeds of 1622.37 still with 39. and there is no default i think. when using 49 it drops drastically to 57.81
                try:
                    subprocess.run(
                        resource_path("") + "lzturbo -39 " +
                        filepath + " " + directory,
                        shell=True,
                        capture_output=True,
                        text=True,
                    )
                except:
                    print("Could not run compressor lzturbo")

    # glza
    def glzacompress(filename, filepath, directory):
        if verbose:
            print("Multicompress glza")
            if compression == CompressionLevel.Strongest:
                try:
                    subprocess.run(
                        resource_path("")
                        + "GLZA c -x "
                        + filepath
                        + " "
                        + directory
                        + "/"
                        + filename
                        + extension11,
                        shell=True,
                    )
                except:
                    print("Could not run compressor GLZA")
            else:
                try:
                    subprocess.run(
                        resource_path("")
                        + "GLZA c "
                        + filepath
                        + " "
                        + directory
                        + "/"
                        + filename
                        + extension11,
                        shell=True,
                    )
                except:
                    print("Could not run compressor GLZA")
        else:
            if compression == CompressionLevel.Strongest:
                try:
                    subprocess.run(
                        resource_path("")
                        + "GLZA c -x "
                        + filepath
                        + " "
                        + directory
                        + "/"
                        + filename
                        + extension11,
                        shell=True,
                        capture_output=True,
                        text=True,
                    )
                except:
                    print("Could not run compressor GLZA")
            else:
                try:
                    subprocess.run(
                        resource_path("")
                        + "GLZA c "
                        + filepath
                        + " "
                        + directory
                        + "/"
                        + filename
                        + extension11,
                        shell=True,
                        capture_output=True,
                        text=True,
                    )
                except:
                    print("Could not run compressor GLZA")

    # balz
    def balzcompress(filename, filepath, directory):
        if verbose:
            print("Multicompress balz")
            if compression == CompressionLevel.Strongest:
                try:
                    subprocess.run(
                        resource_path("")
                        + "balz cx "
                        + filepath
                        + " "
                        + directory
                        + "/"
                        + filename
                        + extension12,
                        shell=True,
                    )
                except:
                    print("Could not run compressor balz")
            else:
                try:
                    subprocess.run(
                        resource_path("")
                        + "balz c "
                        + filepath
                        + " "
                        + directory
                        + "/"
                        + filename
                        + extension12,
                        shell=True,
                    )
                except:
                    print("Could not run compressor balz")
        else:
            if compression == CompressionLevel.Strongest:
                try:
                    subprocess.run(
                        resource_path("")
                        + "balz cx "
                        + filepath
                        + " "
                        + directory
                        + "/"
                        + filename
                        + extension12,
                        shell=True,
                        capture_output=True,
                        text=True,
                    )
                except:
                    print("Could not run compressor balz")
            else:
                try:
                    subprocess.run(
                        resource_path("")
                        + "balz c "
                        + filepath
                        + " "
                        + directory
                        + "/"
                        + filename
                        + extension12,
                        shell=True,
                        capture_output=True,
                        text=True,
                    )
                except:
                    print("Could not run compressor balz")

    # bsc
    def bsccompress(filename, filepath, directory):
        if verbose:
            print("Multicompress bsc")
            if compression == CompressionLevel.Strongest:
                try:
                    subprocess.run(
                        resource_path("")
                        + "bsc e "
                        + filepath
                        + " "
                        + directory
                        + "/"
                        + filename
                        + extension13
                        + " -e2 -b1000",
                        shell=True,
                    )
                except:
                    print("Could not run compressor bsc")
            else:
                try:
                    subprocess.run(
                        resource_path("")
                        + "bsc e "
                        + filepath
                        + " "
                        + directory
                        + "/"
                        + filename
                        + extension13,
                        shell=True,
                    )
                except:
                    print("Could not run compressor bsc")
        else:
            if compression == CompressionLevel.Strongest:
                try:
                    subprocess.run(
                        resource_path("")
                        + "bsc e "
                        + filepath
                        + " "
                        + directory
                        + "/"
                        + filename
                        + extension13
                        + " -e2 -b1000",
                        shell=True,
                        capture_output=True,
                        text=True,
                    )
                except:
                    print("Could not run compressor bsc")
            else:
                try:
                    subprocess.run(
                        resource_path("")
                        + "bsc e "
                        + filepath
                        + " "
                        + directory
                        + "/"
                        + filename
                        + extension13,
                        shell=True,
                        capture_output=True,
                        text=True,
                    )
                except:
                    print("Could not run compressor bsc")

    # csarc
    def csarccompress(filename, filepath, directory):
        if verbose:
            print("Multicompress csarc")
            if compression == CompressionLevel.Strongest:
                try:
                    subprocess.run(
                        resource_path("")
                        + "csarc a -m5 -d1024m "
                        + directory
                        + "/"
                        + filename
                        + extension14
                        + " "
                        + filepath,
                        shell=True,
                    )
                except:
                    print("Could not run compressor csarc")
            else:
                try:
                    subprocess.run(
                        resource_path("")
                        + "csarc a "
                        + directory
                        + "/"
                        + filename
                        + extension14
                        + " "
                        + filepath,
                        shell=True,
                    )
                except:
                    print("Could not run compressor csarc")
        else:
            if compression == CompressionLevel.Strongest:
                try:
                    subprocess.run(
                        resource_path("")
                        + "csarc a -m5 -d1024m "
                        + directory
                        + "/"
                        + filename
                        + extension14
                        + " "
                        + filepath,
                        shell=True,
                        capture_output=True,
                        text=True,
                    )
                except:
                    print("Could not run compressor csarc")
            else:
                try:
                    subprocess.run(
                        resource_path("")
                        + "csarc a "
                        + directory
                        + "/"
                        + filename
                        + extension14
                        + " "
                        + filepath,
                        shell=True,
                        capture_output=True,
                        text=True,
                    )
                except:
                    print("Could not run compressor csarc")

    # nncp (only consecutive and MAX profile)
    def nncpcompress(filename, filepath, directory):
        if verbose:
            print("Compress nncp")
            if compression == CompressionLevel.Max:
                try:
                    subprocess.run(
                        resource_path("")
                        + "nncp c "
                        + filepath
                        + " "
                        + directory
                        + "/"
                        + filename
                        + extension15,
                        shell=True,
                    )
                except:
                    print("Could not run compressor nncp")
        else:
            if compression == CompressionLevel.Max:
                try:
                    subprocess.run(
                        resource_path("")
                        + "nncp c "
                        + filepath
                        + " "
                        + directory
                        + "/"
                        + filename
                        + extension15,
                        shell=True,
                        capture_output=True,
                        text=True,
                    )
                except:
                    print("Could not run compressor nncp")

    # zpaq (only consecutive and MAX profile)
    def zpaqcompress(filename, filepath, directory):
        if verbose:
            print("Compress zpaq")
            if compression == CompressionLevel.Max:
                try:
                    subprocess.run(
                        resource_path("")
                        + "zpaq a "
                        + directory
                        + "/"
                        + filename
                        + extension16
                        + " "
                        + filepath
                        + " -m5",
                        shell=True,
                    )
                except:
                    print("Could not run compressor zpaq")
        else:
            if compression == CompressionLevel.Max:
                try:
                    subprocess.run(
                        resource_path("")
                        + "zpaq a "
                        + directory
                        + "/"
                        + filename
                        + extension16
                        + " "
                        + filepath
                        + " -m5",
                        shell=True,
                        capture_output=True,
                        text=True,
                    )
                except:
                    print("Could not run compressor zpaq")

    # need to iterate all files to find the total number of files to compress for the console output. We cannot use len(files) since this will only show us how many files are in the current subfoler (or in other words, if all files are in the same folder and no subfolders are present, then it would give the same integer, but not otherwise)
    totalNumberOfFiles = 0
    for subdir, dirs, files in os.walk(createFolder):
        for filename in files:
            totalNumberOfFiles = totalNumberOfFiles + 1

    # variable for console output, for "File 3 of 15"
    fileprocesscounter = 0
    # for each file in temporary folder with all copied files (os.walk to iterate over all descendant files in subdirectories)
    # we basically replace each file in the copied files folder (sharetmp) with its min compressed file.
    # we do this by iterating thorugh each file, and for each file creating a temporary directory, where we store the compressed version of this file with each compressor enabled. We then compare compressed file sizes, declare one as the min compressed file, and replace the file in the sharetmp folder with this version (by copying it out of the temporary directory which will be destoryed right after with all its contents)
    for subdir, dirs, files in os.walk(createFolder):
        for filename in files:
            # update filecounter
            fileprocesscounter = fileprocesscounter + 1
            print(
                "Compressing File "
                + str(fileprocesscounter)
                + " of "
                + str(totalNumberOfFiles)
                + " - "
                + os.path.basename(filename)
            )
            # we need these variables for the compressors
            filepathwithoutname = subdir + os.sep
            filepath = subdir + os.sep + filename
            if verbose:
                print("Compressing " + filename + " ...")
            filesizeoriginal = os.stat(filepath).st_size
            # we could sum up foldersize again but it would be of
            # folderSize = folderSize + filesizeoriginal
            # the list of processes for multiprocessing
            processes = []

            # create a temporary directory
            with tempfile.TemporaryDirectory() as directory:
                if verbose:
                    print("The created temporary directory is %s" %
                          directory)

                # add to the processes list with each enabled compressor, so we will start them all concurrently for faster compression

                # zlib
                if compressor0:
                    processes.append(
                        multiprocessing.Process(
                            target=zlibcompress, args=(
                                filename, filepath, directory)
                        )
                    )

                # bz2
                if compressor1:
                    processes.append(
                        multiprocessing.Process(
                            target=bz2compress, args=(
                                filename, filepath, directory)
                        )
                    )

                # lzma/xz
                if compressor2:
                    processes.append(
                        multiprocessing.Process(
                            target=lzmacompress, args=(
                                filename, filepath, directory)
                        )
                    )

                # gzip
                if compressor3:
                    processes.append(
                        multiprocessing.Process(
                            target=gzipcompress, args=(
                                filename, filepath, directory)
                        )
                    )

                # zstd
                if compressor4:
                    processes.append(
                        multiprocessing.Process(
                            target=zstdcompress, args=(
                                filename, filepath, directory)
                        )
                    )

                # ppmd (beta)
                if compressor5:
                    processes.append(
                        multiprocessing.Process(
                            target=ppmdcompress, args=(
                                filename, filepath, directory)
                        )
                    )

                # lz4
                if compressor6:
                    processes.append(
                        multiprocessing.Process(
                            target=lz4compress, args=(
                                filename, filepath, directory)
                        )
                    )

                # brotli
                if compressor7:
                    processes.append(
                        multiprocessing.Process(
                            target=brotlicompress, args=(
                                filename, filepath, directory)
                        )
                    )

                # lzham
                if compressor8:
                    processes.append(
                        multiprocessing.Process(
                            target=lzhamcompress, args=(
                                filename, filepath, directory)
                        )
                    )

                # zopfli
                if compressor9:
                    processes.append(
                        multiprocessing.Process(
                            target=zopflicompress, args=(
                                filename, filepath, directory)
                        )
                    )

                # lzturbo
                if compressor10:
                    processes.append(
                        multiprocessing.Process(
                            target=lzturbocompress, args=(
                                filepath, directory)
                        )
                    )

                # glza
                if compressor11:
                    processes.append(
                        multiprocessing.Process(
                            target=glzacompress, args=(
                                filename, filepath, directory)
                        )
                    )

                # balz
                if compressor12:
                    processes.append(
                        multiprocessing.Process(
                            target=balzcompress, args=(
                                filename, filepath, directory)
                        )
                    )

                # bsc
                if compressor13:
                    processes.append(
                        multiprocessing.Process(
                            target=bsccompress, args=(
                                filename, filepath, directory)
                        )
                    )

                # csarc
                if compressor14:
                    processes.append(
                        multiprocessing.Process(
                            target=csarccompress, args=(
                                filename, filepath, directory)
                        )
                    )

                # memory saver : adjusting the number of concurrent processes (that use RAM)
                if memorySaverLvl == 'Default':
                    # all processes
                    # start multiprocesses
                    for process in processes:
                        process.start()

                    # join multiprocesses
                    for process in processes:
                        process.join()

                # split processes as to reduce memory usage (reduce number of concurrent processes)
                #  in half
                elif memorySaverLvl == 'Low':

                    #  in half
                    processeslist0 = processes[: len(processes) // 2]
                    processeslist1 = processes[len(processes) // 2:]

                    # start multiprocesses first half
                    for process in processeslist0:
                        process.start()

                    # join multiprocesses
                    for process in processeslist0:
                        process.join()

                    # start multiprocesses second half
                    for process in processeslist1:
                        process.start()

                    # join multiprocesses
                    for process in processeslist1:
                        process.join()
                #  in quarters (english language: 'fourths' vs 'quarters'? why a separate word for the exact same thing? Probably adopted from french 'quatre' i'd guess from my school knowledge, but why adapt it instead of a native word that already describes the same thing? In german there is only one word: "vierteln". maybe english often has multiple words for the same thing to describe. Dont know if there is a difference between 'to relax' and 'to chill' either, probably subtle differences that native speakers can differentiate intuitively. even tho 'chill' means cold initially, but maybe is used out of context? but hot-headedness also is meant more for being angry fast than temperature, so 'to chill' in that context would be rather 'to calm down' than 'to relax'. well i guess ill better stop here.)
                elif memorySaverLvl == 'Lower':

                    #  in quarters
                    processeslist0 = processes[: len(processes) // 2]
                    processeslist1 = processes[len(processes) // 2:]
                    processeslist00 = processeslist0[: len(
                        processeslist0) // 2]
                    processeslist01 = processeslist0[len(
                        processeslist0) // 2:]
                    processeslist02 = processeslist1[: len(
                        processeslist1) // 2]
                    processeslist03 = processeslist1[len(
                        processeslist1) // 2:]

                    # start multiprocesses first quarter
                    for process in processeslist00:
                        process.start()

                    # join multiprocesses
                    for process in processeslist00:
                        process.join()

                    # start multiprocesses second quarter
                    for process in processeslist01:
                        process.start()

                    # join multiprocesses
                    for process in processeslist01:
                        process.join()

                    # start multiprocesses third quarter
                    for process in processeslist02:
                        process.start()

                    # join multiprocesses
                    for process in processeslist02:
                        process.join()

                    # start multiprocesses fourth quarter
                    for process in processeslist03:
                        process.start()

                    # join multiprocesses
                    for process in processeslist03:
                        process.join()

                # no parallelization at all, one after another (so for this file start one compressor and join (wait for finish), then start next compressor ...)
                elif memorySaverLvl == 'Lowest':
                    for process in processes:
                        process.start()
                        process.join()

                # MAX mode strong compressors: serial since I ran out of memory when having them concurrently with the other compressions
                if compressor15:
                    nncpcompress(filename, filepath, directory)

                if compressor16:
                    zpaqcompress(filename, filepath, directory)

                # now we continue by comparing compressed sizes of this file

                # list files
                # os.system('cd '+directory+';stat -c " %s %n" *')
                if verbose:
                    os.system("cd " + directory + ";ls -la")

                # Get list of files in directory (0 if zpaq didnt work, 106 for nncp (unsopported cpu architecture for exampe))
                list_of_files = filter(
                    os.path.isfile, glob.glob(directory + "/*"))
                list_of_files_non_zero = [
                    x for x in list_of_files if os.stat(x).st_size != 0 and os.stat(x).st_size != 106
                ]
                # Find the smallest file from the list of files (of non-zero files where compression went wrong)
                min_file = min(list_of_files_non_zero,
                               key=lambda x: os.stat(x).st_size)
                if verbose:
                    print("min File: ", min_file)
                    print("min File size in bytes: ",
                          os.stat(min_file).st_size)

                print(
                    str(filesizeoriginal)
                    + " --> "
                    + str(os.stat(min_file).st_size)
                    + " "
                    + str(os.path.basename(min_file))
                )

                # replace file with smallest compressed file version of itself
                #  # copy compressed file
                try:
                    shutil.copyfile(
                        min_file, filepathwithoutname +
                        os.path.basename(min_file)
                    )
                except:
                    print(
                        colored(
                            "ERROR Could not copy compressed file, file will be missing in archive " +
                            os.path.basename(min_file),
                            "red",
                        )
                    )

                # add to compressor original file array
                if os.path.splitext(min_file)[1] == extension0:
                    compressor0OriginalsArray.append(
                        filepath)
                if os.path.splitext(min_file)[1] == extension1:
                    compressor1OriginalsArray.append(
                        filepath)
                if os.path.splitext(min_file)[1] == extension2:
                    compressor2OriginalsArray.append(
                        filepath)
                if os.path.splitext(min_file)[1] == extension3:
                    compressor3OriginalsArray.append(
                        filepath)
                if os.path.splitext(min_file)[1] == extension4:
                    compressor4OriginalsArray.append(
                        filepath)
                if os.path.splitext(min_file)[1] == extension5:
                    compressor5OriginalsArray.append(
                        filepath)
                if os.path.splitext(min_file)[1] == extension6:
                    compressor6OriginalsArray.append(
                        filepath)
                if os.path.splitext(min_file)[1] == extension7:
                    compressor7OriginalsArray.append(
                        filepath)
                if os.path.splitext(min_file)[1] == extension8:
                    compressor8OriginalsArray.append(
                        filepath)
                if os.path.splitext(min_file)[1] == extension9:
                    compressor9OriginalsArray.append(
                        filepath)
                if os.path.splitext(min_file)[1] == extension10:
                    compressor10OriginalsArray.append(
                        filepath)
                if os.path.splitext(min_file)[1] == extension11:
                    compressor11OriginalsArray.append(
                        filepath)
                if os.path.splitext(min_file)[1] == extension12:
                    compressor12OriginalsArray.append(
                        filepath)
                if os.path.splitext(min_file)[1] == extension13:
                    compressor13OriginalsArray.append(
                        filepath)
                if os.path.splitext(min_file)[1] == extension14:
                    compressor14OriginalsArray.append(
                        filepath)
                if os.path.splitext(min_file)[1] == extension15:
                    compressor15OriginalsArray.append(
                        filepath)
                if os.path.splitext(min_file)[1] == extension16:
                    compressor16OriginalsArray.append(
                        filepath)

                # add to compressor compressed file array
                if os.path.splitext(min_file)[1] == extension0:
                    compressor0CompressedArray.append(
                        filepathwithoutname + os.path.basename(min_file))
                if os.path.splitext(min_file)[1] == extension1:
                    compressor1CompressedArray.append(
                        filepathwithoutname + os.path.basename(min_file))
                if os.path.splitext(min_file)[1] == extension2:
                    compressor2CompressedArray.append(
                        filepathwithoutname + os.path.basename(min_file))
                if os.path.splitext(min_file)[1] == extension3:
                    compressor3CompressedArray.append(
                        filepathwithoutname + os.path.basename(min_file))
                if os.path.splitext(min_file)[1] == extension4:
                    compressor4CompressedArray.append(
                        filepathwithoutname + os.path.basename(min_file))
                if os.path.splitext(min_file)[1] == extension5:
                    compressor5CompressedArray.append(
                        filepathwithoutname + os.path.basename(min_file))
                if os.path.splitext(min_file)[1] == extension6:
                    compressor6CompressedArray.append(
                        filepathwithoutname + os.path.basename(min_file))
                if os.path.splitext(min_file)[1] == extension7:
                    compressor7CompressedArray.append(
                        filepathwithoutname + os.path.basename(min_file))
                if os.path.splitext(min_file)[1] == extension8:
                    compressor8CompressedArray.append(
                        filepathwithoutname + os.path.basename(min_file))
                if os.path.splitext(min_file)[1] == extension9:
                    compressor9CompressedArray.append(
                        filepathwithoutname + os.path.basename(min_file))
                if os.path.splitext(min_file)[1] == extension10:
                    compressor10CompressedArray.append(
                        filepathwithoutname + os.path.basename(min_file))
                if os.path.splitext(min_file)[1] == extension11:
                    compressor11CompressedArray.append(
                        filepathwithoutname + os.path.basename(min_file))
                if os.path.splitext(min_file)[1] == extension12:
                    compressor12CompressedArray.append(
                        filepathwithoutname + os.path.basename(min_file))
                if os.path.splitext(min_file)[1] == extension13:
                    compressor13CompressedArray.append(
                        filepathwithoutname + os.path.basename(min_file))
                if os.path.splitext(min_file)[1] == extension14:
                    compressor14CompressedArray.append(
                        filepathwithoutname + os.path.basename(min_file))
                if os.path.splitext(min_file)[1] == extension15:
                    compressor15CompressedArray.append(
                        filepathwithoutname + os.path.basename(min_file))
                if os.path.splitext(min_file)[1] == extension16:
                    compressor16CompressedArray.append(
                        filepathwithoutname + os.path.basename(min_file))

                # # delete uncompressed file
                # if os.path.exists(filepath):
                #     os.remove(filepath)
                # else:
                #     print(
                #         colored(
                #             "ERROR Could not delete uncompressed file, archive will have uncompressed file inculded",
                #             "red",
                #         )
                #     )
                if verbose:
                    print("Compressing " +
                          os.path.basename(filepath) + " DONE")

    # if there is a single compressed file of a compressor, we remove the uncompressed/original output file
    if len(compressor0OriginalsArray) == 1:
        # delete uncompressed file
        if os.path.exists(compressor0OriginalsArray[0]):
            os.remove(compressor0OriginalsArray[0])
        else:
            print(
                colored(
                    "ERROR Could not delete uncompressed file, archive will have uncompressed file inculded",
                    "red",
                )
            )
    if len(compressor1OriginalsArray) == 1:
        # delete uncompressed file
        if os.path.exists(compressor1OriginalsArray[0]):
            os.remove(compressor1OriginalsArray[0])
        else:
            print(
                colored(
                    "ERROR Could not delete uncompressed file, archive will have uncompressed file inculded",
                    "red",
                )
            )
    if len(compressor2OriginalsArray) == 1:
        # delete uncompressed file
        if os.path.exists(compressor2OriginalsArray[0]):
            os.remove(compressor2OriginalsArray[0])
        else:
            print(
                colored(
                    "ERROR Could not delete uncompressed file, archive will have uncompressed file inculded",
                    "red",
                )
            )
    if len(compressor3OriginalsArray) == 1:
        # delete uncompressed file
        if os.path.exists(compressor3OriginalsArray[0]):
            os.remove(compressor3OriginalsArray[0])
        else:
            print(
                colored(
                    "ERROR Could not delete uncompressed file, archive will have uncompressed file inculded",
                    "red",
                )
            )
    if len(compressor4OriginalsArray) == 1:
        # delete uncompressed file
        if os.path.exists(compressor4OriginalsArray[0]):
            os.remove(compressor4OriginalsArray[0])
        else:
            print(
                colored(
                    "ERROR Could not delete uncompressed file, archive will have uncompressed file inculded",
                    "red",
                )
            )
    if len(compressor5OriginalsArray) == 1:
        # delete uncompressed file
        if os.path.exists(compressor5OriginalsArray[0]):
            os.remove(compressor5OriginalsArray[0])
        else:
            print(
                colored(
                    "ERROR Could not delete uncompressed file, archive will have uncompressed file inculded",
                    "red",
                )
            )
    if len(compressor6OriginalsArray) == 1:
        # delete uncompressed file
        if os.path.exists(compressor6OriginalsArray[0]):
            os.remove(compressor6OriginalsArray[0])
        else:
            print(
                colored(
                    "ERROR Could not delete uncompressed file, archive will have uncompressed file inculded",
                    "red",
                )
            )
    if len(compressor7OriginalsArray) == 1:
        # delete uncompressed file
        if os.path.exists(compressor7OriginalsArray[0]):
            os.remove(compressor7OriginalsArray[0])
        else:
            print(
                colored(
                    "ERROR Could not delete uncompressed file, archive will have uncompressed file inculded",
                    "red",
                )
            )
    if len(compressor8OriginalsArray) == 1:
        # delete uncompressed file
        if os.path.exists(compressor8OriginalsArray[0]):
            os.remove(compressor8OriginalsArray[0])
        else:
            print(
                colored(
                    "ERROR Could not delete uncompressed file, archive will have uncompressed file inculded",
                    "red",
                )
            )
    if len(compressor9OriginalsArray) == 1:
        # delete uncompressed file
        if os.path.exists(compressor9OriginalsArray[0]):
            os.remove(compressor9OriginalsArray[0])
        else:
            print(
                colored(
                    "ERROR Could not delete uncompressed file, archive will have uncompressed file inculded",
                    "red",
                )
            )
    if len(compressor10OriginalsArray) == 1:
        # delete uncompressed file
        if os.path.exists(compressor10OriginalsArray[0]):
            os.remove(compressor10OriginalsArray[0])
        else:
            print(
                colored(
                    "ERROR Could not delete uncompressed file, archive will have uncompressed file inculded",
                    "red",
                )
            )
    if len(compressor11OriginalsArray) == 1:
        # delete uncompressed file
        if os.path.exists(compressor11OriginalsArray[0]):
            os.remove(compressor11OriginalsArray[0])
        else:
            print(
                colored(
                    "ERROR Could not delete uncompressed file, archive will have uncompressed file inculded",
                    "red",
                )
            )
    if len(compressor12OriginalsArray) == 1:
        # delete uncompressed file
        if os.path.exists(compressor12OriginalsArray[0]):
            os.remove(compressor12OriginalsArray[0])
        else:
            print(
                colored(
                    "ERROR Could not delete uncompressed file, archive will have uncompressed file inculded",
                    "red",
                )
            )
    if len(compressor13OriginalsArray) == 1:
        # delete uncompressed file
        if os.path.exists(compressor13OriginalsArray[0]):
            os.remove(compressor13OriginalsArray[0])
        else:
            print(
                colored(
                    "ERROR Could not delete uncompressed file, archive will have uncompressed file inculded",
                    "red",
                )
            )
    if len(compressor14OriginalsArray) == 1:
        # delete uncompressed file
        if os.path.exists(compressor14OriginalsArray[0]):
            os.remove(compressor14OriginalsArray[0])
        else:
            print(
                colored(
                    "ERROR Could not delete uncompressed file, archive will have uncompressed file inculded",
                    "red",
                )
            )
    if len(compressor15OriginalsArray) == 1:
        # delete uncompressed file
        if os.path.exists(compressor15OriginalsArray[0]):
            os.remove(compressor15OriginalsArray[0])
        else:
            print(
                colored(
                    "ERROR Could not delete uncompressed file, archive will have uncompressed file inculded",
                    "red",
                )
            )
    if len(compressor16OriginalsArray) == 1:
        # delete uncompressed file
        if os.path.exists(compressor16OriginalsArray[0]):
            os.remove(compressor16OriginalsArray[0])
        else:
            print(
                colored(
                    "ERROR Could not delete uncompressed file, archive will have uncompressed file inculded",
                    "red",
                )
            )

    def removefile(filepath):
        if os.path.exists(filepath):
            os.remove(filepath)
        else:
            print(
                colored(
                    "ERROR Could not delete singly compressed file, archive will have uncompressed file inculded",
                    "red",
                )
            )

    # else we actually delete the single compressed files, and then recompress all of these files together for this compressor in one single command, so the compressor can take care of inter-file redundancies
    if len(compressor0CompressedArray) > 1:
        for arrayFilepath in compressor0CompressedArray:
            removefile(arrayFilepath)
    if len(compressor1CompressedArray) > 1:
        for arrayFilepath in compressor1CompressedArray:
            removefile(arrayFilepath)
    if len(compressor2CompressedArray) > 1:
        for arrayFilepath in compressor2CompressedArray:
            removefile(arrayFilepath)
    if len(compressor3CompressedArray) > 1:
        for arrayFilepath in compressor3CompressedArray:
            removefile(arrayFilepath)
    if len(compressor4CompressedArray) > 1:
        for arrayFilepath in compressor4CompressedArray:
            removefile(arrayFilepath)
    if len(compressor5CompressedArray) > 1:
        for arrayFilepath in compressor5CompressedArray:
            removefile(arrayFilepath)
    if len(compressor6CompressedArray) > 1:
        for arrayFilepath in compressor6CompressedArray:
            removefile(arrayFilepath)
    if len(compressor7CompressedArray) > 1:
        for arrayFilepath in compressor7CompressedArray:
            removefile(arrayFilepath)
    if len(compressor8CompressedArray) > 1:
        for arrayFilepath in compressor8CompressedArray:
            removefile(arrayFilepath)
    if len(compressor9CompressedArray) > 1:
        for arrayFilepath in compressor9CompressedArray:
            removefile(arrayFilepath)
    if len(compressor10CompressedArray) > 1:
        for arrayFilepath in compressor10CompressedArray:
            removefile(arrayFilepath)
    if len(compressor11CompressedArray) > 1:
        for arrayFilepath in compressor11CompressedArray:
            removefile(arrayFilepath)
    if len(compressor12CompressedArray) > 1:
        for arrayFilepath in compressor12CompressedArray:
            removefile(arrayFilepath)
    if len(compressor13CompressedArray) > 1:
        for arrayFilepath in compressor13CompressedArray:
            removefile(arrayFilepath)
    if len(compressor14CompressedArray) > 1:
        for arrayFilepath in compressor14CompressedArray:
            removefile(arrayFilepath)
    if len(compressor15CompressedArray) > 1:
        for arrayFilepath in compressor15CompressedArray:
            removefile(arrayFilepath)
    if len(compressor16CompressedArray) > 1:
        for arrayFilepath in compressor16CompressedArray:
            removefile(arrayFilepath)

    # *Recompress*
    # recompress files with specific compressor in one command. We left the original files untouched (if there were single files for a compressor, we deleted the original files. If there are more, we deleted the singly compressed files)
    filesToCompressString = ""

    print("Recompress files to account for inter-file redundancy")

    # should we simply put all these files in a .tar archive, and then run the normal compression method we already defined?

    directory = os.path.abspath("./sharetmp")

    # zlib
    if len(compressor0OriginalsArray) > 1:

        print("...with zlib: ", end='')

        filename = 'zlib.tar'
        filepath = os.path.abspath(directory+"/"+filename)

        with tarfile.open(filepath, mode='w') as tar:
            for arrayFilepath in compressor0OriginalsArray:
                print(str(os.path.basename(arrayFilepath))+' ', end='')
                tar.add(arrayFilepath)
                removefile(arrayFilepath)

        zlibcompress(filename, filepath, directory)
        removefile(filepath)

        newfile = filepath+'.zlib'
        print(" --> "+str(os.stat(newfile).st_size) +
              " " + str(os.path.basename(newfile)))

    # bz2
    if len(compressor1OriginalsArray) > 1:

        print("...with bz2: ", end='')

        filename = 'bz2.tar'
        filepath = os.path.abspath(directory+"/"+filename)

        with tarfile.open(filepath, mode='w') as tar:
            for arrayFilepath in compressor1OriginalsArray:
                print(os.path.basename(arrayFilepath)+' ', end='')
                tar.add(arrayFilepath)
                removefile(arrayFilepath)

        bz2compress(filename, filepath, directory)
        removefile(filepath)

        newfile = filepath+'.bz2'
        print(" --> "+str(os.stat(newfile).st_size) +
              " " + str(os.path.basename(newfile)))

    # xz
    if len(compressor2OriginalsArray) > 1:

        print("...with xz: ", end='')

        filename = 'xz.tar'
        filepath = os.path.abspath(directory+"/"+filename)

        with tarfile.open(filepath, mode='w') as tar:
            for arrayFilepath in compressor2OriginalsArray:
                print(os.path.basename(arrayFilepath)+' ', end='')
                tar.add(arrayFilepath)
                removefile(arrayFilepath)

        lzmacompress(filename, filepath, directory)
        removefile(filepath)

        newfile = filepath+'.xz'
        print(" --> "+str(os.stat(newfile).st_size) +
              " " + str(os.path.basename(newfile)))

    # gz
    if len(compressor3OriginalsArray) > 1:

        print("...with gz: ", end='')

        filename = 'gz.tar'
        filepath = os.path.abspath(directory+"/"+filename)

        with tarfile.open(filepath, mode='w') as tar:
            for arrayFilepath in compressor3OriginalsArray:
                print(os.path.basename(arrayFilepath)+' ', end='')
                tar.add(arrayFilepath)
                removefile(arrayFilepath)

        gzipcompress(filename, filepath, directory)
        removefile(filepath)

        newfile = filepath+'.gz'
        print(" --> "+str(os.stat(newfile).st_size) +
              " " + str(os.path.basename(newfile)))

    # zst
    if len(compressor4OriginalsArray) > 1:

        print("...with zst: ", end='')

        filename = 'zst.tar'
        filepath = os.path.abspath(directory+"/"+filename)

        with tarfile.open(filepath, mode='w') as tar:
            for arrayFilepath in compressor4OriginalsArray:
                print(os.path.basename(arrayFilepath)+' ', end='')
                tar.add(arrayFilepath)
                removefile(arrayFilepath)

        zstdcompress(filename, filepath, directory)
        removefile(filepath)

        newfile = filepath+'.zst'
        print(" --> "+str(os.stat(newfile).st_size) +
              " " + str(os.path.basename(newfile)))

    # ppmd
    if len(compressor5OriginalsArray) > 1:

        print("...with ppmd: ", end='')

        filename = 'ppmd.tar'
        filepath = os.path.abspath(directory+"/"+filename)

        with tarfile.open(filepath, mode='w') as tar:
            for arrayFilepath in compressor5OriginalsArray:
                print(os.path.basename(arrayFilepath)+' ', end='')
                tar.add(arrayFilepath)
                removefile(arrayFilepath)

        ppmdcompress(filename, filepath, directory)
        removefile(filepath)

        newfile = filepath+'.ppmd'
        print(" --> "+str(os.stat(newfile).st_size) +
              " " + str(os.path.basename(newfile)))

    # lz4
    if len(compressor6OriginalsArray) > 1:

        print("...with lz4: ", end='')

        filename = 'lz4.tar'
        filepath = os.path.abspath(directory+"/"+filename)

        with tarfile.open(filepath, mode='w') as tar:
            for arrayFilepath in compressor6OriginalsArray:
                print(os.path.basename(arrayFilepath)+' ', end='')
                tar.add(arrayFilepath)
                removefile(arrayFilepath)

        lz4compress(filename, filepath, directory)
        removefile(filepath)

        newfile = filepath+'.lz4'
        print(" --> "+str(os.stat(newfile).st_size) +
              " " + str(os.path.basename(newfile)))

    # brotli
    if len(compressor7OriginalsArray) > 1:

        print("...with brotli: ", end='')

        filename = 'brotli.tar'
        filepath = os.path.abspath(directory+"/"+filename)

        with tarfile.open(filepath, mode='w') as tar:
            for arrayFilepath in compressor7OriginalsArray:
                print(os.path.basename(arrayFilepath)+' ', end='')
                tar.add(arrayFilepath)
                removefile(arrayFilepath)

        brotlicompress(filename, filepath, directory)
        removefile(filepath)

        newfile = filepath+'.brotli'
        print(" --> "+str(os.stat(newfile).st_size) +
              " " + str(os.path.basename(newfile)))

    # lzham
    if len(compressor8OriginalsArray) > 1:

        print("...with lzham: ", end='')

        filename = 'lzham.tar'
        filepath = os.path.abspath(directory+"/"+filename)

        with tarfile.open(filepath, mode='w') as tar:
            for arrayFilepath in compressor8OriginalsArray:
                print(os.path.basename(arrayFilepath)+' ', end='')
                tar.add(arrayFilepath)
                removefile(arrayFilepath)

        lzhamcompress(filename, filepath, directory)
        removefile(filepath)

        newfile = filepath+'.lzham'
        print(" --> "+str(os.stat(newfile).st_size) +
              " " + str(os.path.basename(newfile)))

    # zopfli
    if len(compressor9OriginalsArray) > 1:

        print("...with zopfli: ", end='')

        filename = 'zopfli.tar'
        filepath = os.path.abspath(directory+"/"+filename)

        with tarfile.open(filepath, mode='w') as tar:
            for arrayFilepath in compressor9OriginalsArray:
                print(os.path.basename(arrayFilepath)+' ', end='')
                tar.add(arrayFilepath)
                removefile(arrayFilepath)

        zopflicompress(filename, filepath, directory)
        removefile(filepath)

        newfile = filepath+'.zopfli'
        print(" --> "+str(os.stat(newfile).st_size) +
              " " + str(os.path.basename(newfile)))

    # lzt
    if len(compressor10OriginalsArray) > 1:

        print("...with lzt: ", end='')

        filename = 'lzt.tar'
        filepath = os.path.abspath(directory+"/"+filename)

        with tarfile.open(filepath, mode='w') as tar:
            for arrayFilepath in compressor10OriginalsArray:
                print(os.path.basename(arrayFilepath)+' ', end='')
                tar.add(arrayFilepath)
                removefile(arrayFilepath)

        lzturbocompress(filepath, directory)
        removefile(filepath)

        newfile = filepath+'.lzt'
        print(" --> "+str(os.stat(newfile).st_size) +
              " " + str(os.path.basename(newfile)))

    # glza
    if len(compressor11OriginalsArray) > 1:

        print("...with glza: ", end='')

        filename = 'glza.tar'
        filepath = os.path.abspath(directory+"/"+filename)

        with tarfile.open(filepath, mode='w') as tar:
            for arrayFilepath in compressor11OriginalsArray:
                print(os.path.basename(arrayFilepath)+' ', end='')
                tar.add(arrayFilepath)
                removefile(arrayFilepath)

        glzacompress(filename, filepath, directory)
        removefile(filepath)

        newfile = filepath+'.glza'
        print(" --> "+str(os.stat(newfile).st_size) +
              " " + str(os.path.basename(newfile)))

    # balz
    if len(compressor12OriginalsArray) > 1:

        print("...with balz: ", end='')

        filename = 'balz.tar'
        filepath = os.path.abspath(directory+"/"+filename)

        with tarfile.open(filepath, mode='w') as tar:
            for arrayFilepath in compressor12OriginalsArray:
                print(os.path.basename(arrayFilepath)+' ', end='')
                tar.add(arrayFilepath)
                removefile(arrayFilepath)

        balzcompress(filename, filepath, directory)
        removefile(filepath)

        newfile = filepath+'.balz'
        print(" --> "+str(os.stat(newfile).st_size) +
              " " + str(os.path.basename(newfile)))

    # bsc
    if len(compressor13OriginalsArray) > 1:

        print("...with bsc: ", end='')

        filename = 'bsc.tar'
        filepath = os.path.abspath(directory+"/"+filename)

        with tarfile.open(filepath, mode='w') as tar:
            for arrayFilepath in compressor13OriginalsArray:
                print(os.path.basename(arrayFilepath)+' ', end='')
                tar.add(arrayFilepath)
                removefile(arrayFilepath)

        bsccompress(filename, filepath, directory)
        removefile(filepath)

        newfile = filepath+'.bsc'
        print(" --> "+str(os.stat(newfile).st_size) +
              " " + str(os.path.basename(newfile)))

    # csa
    if len(compressor14OriginalsArray) > 1:

        print("...with csa: ", end='')

        filename = 'csa.tar'
        filepath = os.path.abspath(directory+"/"+filename)

        with tarfile.open(filepath, mode='w') as tar:
            for arrayFilepath in compressor14OriginalsArray:
                print(os.path.basename(arrayFilepath)+' ', end='')
                tar.add(arrayFilepath)
                removefile(arrayFilepath)

        csarccompress(filename, filepath, directory)
        removefile(filepath)

        newfile = filepath+'.csa'
        print(" --> "+str(os.stat(newfile).st_size) +
              " " + str(os.path.basename(newfile)))

    # nncp
    if len(compressor15OriginalsArray) > 1:

        print("...with nncp: ", end='')

        filename = 'nncp.tar'
        filepath = os.path.abspath(directory+"/"+filename)

        with tarfile.open(filepath, mode='w') as tar:
            for arrayFilepath in compressor15OriginalsArray:
                print(os.path.basename(arrayFilepath)+' ', end='')
                tar.add(arrayFilepath)
                removefile(arrayFilepath)

        nncpcompress(filename, filepath, directory)
        removefile(filepath)

        newfile = filepath+'.nncp'
        print(" --> "+str(os.stat(newfile).st_size) +
              " " + str(os.path.basename(newfile)))

    # zpaq
    if len(compressor16OriginalsArray) > 1:

        print("...with zpaq: ", end='')

        filename = 'zpaq.tar'
        filepath = os.path.abspath(directory+"/"+filename)

        with tarfile.open(filepath, mode='w') as tar:
            for arrayFilepath in compressor16OriginalsArray:
                print(os.path.basename(arrayFilepath)+' ', end='')
                tar.add(arrayFilepath)
                removefile(arrayFilepath)

        zpaqcompress(filename, filepath, directory)
        removefile(filepath)

        newfile = filepath+'.zpaq'
        print(" --> "+str(os.stat(newfile).st_size) +
              " " + str(os.path.basename(newfile)))

    # directory and its contents have been removed by this point
    if verbose:
        print("Creating archive")
    # add compressing system information to archive by extending and adding the info.json file. We can also use this to compare archives by compression ratio, compression time, if we use compare action and give archives with different levels or zip comparison archive as input
    with open(resource_path("") + "info.json") as json_file:
        jsondata = json.load(json_file)
        jsondata.update(
            {
                "os.name": os.name,
                "platform.system": platform.system(),
                "platform.release": platform.release(),
                "originalsize": folderSize,
                "compressiontime": round(time.time() - start_time, 2),
                "compressionlevel": str(compression),
            }
        )
    with open(createFolder + "/info.json", "w") as outfile:
        json.dump(jsondata, outfile)

    # tar the compressed folder content and name as .share archive
    with tarfile.open(output_path + "/" + os.path.basename(input_path) + ".share", "w") as tar:
        tar.add(createFolder, arcname="/")
    if verbose:
        print("Archive created")

    # console print out some information
    print("Original Size: " + str(folderSize))
    archiveSize = os.stat(output_path + "/" +
                          os.path.basename(input_path) + ".share").st_size
    print("Archive Size: " + str(archiveSize))
    print(colored("Compression Ratio: ", "green") +
          str(folderSize / archiveSize))

    # remove the copy folder
    if verbose:
        print("Deletion of the directory %s " % createFolder)
    shutil.rmtree(createFolder, ignore_errors=True)

    print(
        colored("Program Execution Time (PET): ", "magenta")
        + str(round(time.time() - start_time, 2))
        + " seconds"
    )

    # COMPRESSION SECTION COMPLETE


def DECOMPRESS(inputShareFile, outputDir, memorySaverLvl):
    print("decompress")
    input_path = inputShareFile
    output_path = outputDir
    # prevent output path errors. rather than creating this path automatically, have the user create it manually as to not create whole paths/folder trees if the user entered a non exitsting path
    # for compression I check here if archive already exists, if yes, we show error instead of overwriting existing archive
    # for decompression I check if extraction folder that will be generated already exists. Othwerise, my application will decompress all compatible compressed files within that folder, doesnt matter if they originally were in the archive to be decompressed or not. The user might not want this behavior

    if not os.path.isdir(output_path):
        print(
            colored("ERROR: The output folder path specified does not exist", "red"))
        sys.exit()
    # if the extraction folder to generate already exists, display merror essage here. We do not want to overwrite existing data.
    if input_path.rfind("/") != -1:
        nameOfArchive = input_path[input_path.rfind(
            "/") + 1:].replace(".share", "")
    else:
        nameOfArchive = input_path.replace(".share", "")

    if output_path.endswith("/"):
        pathForExtractionFolder = output_path + nameOfArchive
    else:
        pathForExtractionFolder = output_path + "/" + nameOfArchive

    if os.path.exists(pathForExtractionFolder):
        print(colored("ERROR: " + pathForExtractionFolder + "already exists", "red"))
        print(
            "Decompression has been cancelled. It tried to create a directory with the same name as the share archive provided in the given output, but it already exists. To prevent data loss, manual action is required for this decompression command to work: You can either delete "
            + pathForExtractionFolder
            + " or provide a different output path or rename the share archive as this will create a different extraction directory"
        )
        sys.exit()

    if memorySaverLvl != 0:
        print(colored("Memory Saver Active with Level " + str(memorySaverLvl), "cyan"))

    # delete sharetmp folder if still exists from for example manually interrupted compression with Ctrl+C previously.
    if os.path.exists(os.getcwd() + "/sharetmp"):
        shutil.rmtree(os.getcwd() + "/sharetmp")

    # if interruption, clean up tmp folder

    def signal_handle(_signal, frame):
        print("Interruption. Stopping the Jobs and cleaning up. Please wait ...")
        if os.path.exists(os.getcwd() + "/sharetmp"):
            shutil.rmtree(os.getcwd() + "/sharetmp")

    signal.signal(signal.SIGINT, signal_handle)

    # timer, start tracking time for output
    start_time = time.time()  # for monitoring execution time

    # for pyinstaller single executable file
    # get the path to the temporary folder created by pyinstaller

    def resource_path(relative_path):
        """Get absolute path to resource, works for dev and for PyInstaller"""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    # ACTIONS (see other atcions below)

    # to decompress, we create a folder with the same name as the input archive name.
    # we then go thorugh each file, replacing it with its decompressed version.
    try:
        os.mkdir(pathForExtractionFolder)
    except OSError:
        print(
            colored(
                "Decompression stopped: Could not create extraction directory", "red"
            )
        )
        sys.exit()
    else:
        print("Successfully created extraction directory ")

    # copy all files from archive into that extraction folder while preserving folder structure
    my_tar = tarfile.open(input_path)
    my_tar.extractall(pathForExtractionFolder)
    my_tar.close()

    # decompression commands
    def decompress(filepath, filename):
        filepathwithoutextension = os.path.splitext(filepath)[0]

        print("Decompressing " + filename + " ...")

        # zlib
        if filename.endswith(extension0):
            with open(filepath, mode="rb") as fin, open(
                filepathwithoutextension, "wb"
            ) as fout:
                data = fin.read()
                decompressed_data = zlib.decompress(data)
                fout.write(decompressed_data)

        # #bz2
        if filename.endswith(extension1):
            with bz2.open(filepath, "rb") as fin, open(
                filepathwithoutextension, "wb"
            ) as fout:
                decompressed_data = fin.read()
                fout.write(decompressed_data)

        # #lzma/xz
        if filename.endswith(extension2):
            with open(filepath, mode="rb") as fin, open(
                filepathwithoutextension, "wb"
            ) as fout:
                data = fin.read()
                decompressed_data = lzma.decompress(data)
                fout.write(decompressed_data)

        # #gzip
        if filename.endswith(extension3):
            with gzip.open(filepath, "rb") as fin, open(
                filepathwithoutextension, "wb"
            ) as fout:
                decompressed_data = fin.read()
                fout.write(decompressed_data)

        # zst
        if filename.endswith(extension4):
            with open(filepath, mode="rb") as fin, open(
                filepathwithoutextension, "wb"
            ) as fout:
                data = fin.read()
                decompressed_data = zstd.decompress(data)
                fout.write(decompressed_data)

        # ppmd
        if filename.endswith(extension5):
            with open(filepath, mode="rb") as fin, open(
                filepathwithoutextension, "wb"
            ) as fout:
                data = fin.read()
                decompressed_data = pyppmd.decompress(data)
                fout.write(decompressed_data)

        # lz4
        if filename.endswith(extension6):
            with open(filepath, mode="rb") as fin, open(
                filepathwithoutextension, "wb"
            ) as fout:
                data = fin.read()
                decompressed_data = lz4.frame.decompress(data)
                fout.write(decompressed_data)

        # brotli
        if filename.endswith(extension7):
            with open(filepath, mode="rb") as fin, open(
                filepathwithoutextension, "wb"
            ) as fout:
                data = fin.read()
                decompressed_data = brotli.decompress(data)
                fout.write(decompressed_data)

        # lzham
        # what we are doing here: to decompress, we need to give as an argument/header the uncompressed file size. Normally this is stored in the lzham header, but the dev of this library did not know about it/indluce it.
        # there is a pull request pending with integrating header but has not been merged
        # this is why i store this information in the filename, and extract it from the filename to decompress. of course, for the end user, this will be cleaned up.
        if filename.endswith(extension8):
            cleanfilename = os.path.basename(filepathwithoutextension)[
                : os.path.basename(filepathwithoutextension).rindex("__")
            ]
            uncompressedsize = int(
                os.path.basename(filepathwithoutextension)[
                    os.path.basename(filepathwithoutextension).rindex("__") + 2:
                ]
            )

            with open(filepath, mode="rb") as fin, open(
                subdir + os.sep + cleanfilename, "wb"
            ) as fout:
                data = fin.read()
                decompressed_data = lzham.decompress(
                    data, uncompressedsize)
                fout.write(decompressed_data)

        # zopfli
        if filename.endswith(extension9):
            with open(filepath, mode="rb") as fin, open(
                filepathwithoutextension, "wb"
            ) as fout:
                data = fin.read()
                decompressed_data = zlib.decompress(data)
                fout.write(decompressed_data)

        # external applications included with pyinstaller

        # lzturbo
        if filename.endswith(extension10):
            try:
                subprocess.run(
                    resource_path("")
                    + "lzturbo -d "
                    + filepath
                    + " "
                    + filepathwithoutextension,
                    shell=True,
                    capture_output=True,
                    text=True,
                )
            except:
                print("Could not use decompressor lzturbo")

        # glza
        if filename.endswith(extension11):
            try:
                subprocess.run(
                    resource_path("")
                    + "GLZA d "
                    + filepath
                    + " "
                    + filepathwithoutextension,
                    shell=True,
                    capture_output=True,
                    text=True,
                )
            except:
                print("Could not use decompressor GLZA")

        # balz
        if filename.endswith(extension12):
            try:
                subprocess.run(
                    resource_path("")
                    + "balz d "
                    + filepath
                    + " "
                    + filepathwithoutextension,
                    shell=True,
                    capture_output=True,
                    text=True,
                )
            except:
                print("Could not use decompressor balz")

        # bsc
        if filename.endswith(extension13):
            try:
                subprocess.run(
                    resource_path("")
                    + "bsc d "
                    + filepath
                    + " "
                    + filepathwithoutextension,
                    shell=True,
                    capture_output=True,
                    text=True,
                )
            except:
                print("Could not use decompressor bsc")

        # csarc
        if filename.endswith(extension14):
            # tmp. directory since csarc somehow includes fill path to file, so when decompressing we ignore filestructure and search for a decompressed file and then copy it out of the tmp directory into the correct extraction directory
            with tempfile.TemporaryDirectory() as tmpdirname:
                try:
                    subprocess.run(
                        resource_path("")
                        + "csarc x -o "
                        + tmpdirname
                        + os.sep
                        + " "
                        + filepath,
                        shell=True,
                        capture_output=True,
                        text=True,
                    )
                except:
                    print("Could not use decompressor csarc")

                for dirpath, dirname, filenames in os.walk(tmpdirname):
                    print(dirpath)
                    print(dirname)
                    print(filenames)
                    for filename in [f for f in filenames]:
                        print(filename)
                        file = os.path.join(dirpath, filename)

                # copy file into extraction folder
                shutil.copy(file, subdir + os.sep + filename)
            # tmp directory and contents have been removed

        # nncp
        if filename.endswith(extension15):
            try:
                subprocess.run(
                    resource_path("")
                    + "nncp d "
                    + filepath
                    + " "
                    + filepathwithoutextension,
                    shell=True,
                    capture_output=True,
                    text=True,
                )
            except:
                print("Could not use decompressor nncp")

        # zpaq
        if filename.endswith(extension16):
            # tmp. directory since csarc somehow includes fill path to file, so when decompressing we ignore filestructure and search for a decompressed file and then copy it out of the tmp directory into the correct extraction directory
            with tempfile.TemporaryDirectory() as tmpdirname:
                try:
                    subprocess.run(
                        resource_path("")
                        + "zpaq x "
                        + filepath
                        + " -to "
                        + tmpdirname
                        + os.sep
                        + output_path
                        + "/zpaq",
                        shell=True,
                        capture_output=True,
                        text=True,
                    )
                except:
                    print("Could not use decompressor zpaq")

                for dirpath, dirname, filenames in os.walk(tmpdirname):
                    for filename in [f for f in filenames]:
                        file = os.path.join(dirpath, filename)

                # copy file into extraction folder
                shutil.copy(file, subdir + os.sep + filename)
            # tmp directory and contents have been removed

        # delete compressed file
        if os.path.exists(filepath):
            os.remove(filepath)
        else:
            print(
                "There is a compressed file still in your extracted folder: " + filename
            )

        # for each file in that folder (os.walk to iterate over all descendant files in subdirectories)
    strongFileList = []
    processes = []

    for subdir, dirs, files in os.walk(pathForExtractionFolder):
        for filename in files:
            filepath = subdir + os.sep + filename

            # the infofile we added for information. Use for internal purposes/debugging but delete from extraction.
            if filename.endswith(".json"):

                with open(filepath) as json_file:
                    jsondata = json.load(json_file)
                    print(
                        "Archive Information: Compressed with "
                        + jsondata["application"]
                        + " Version "
                        + jsondata["version"]
                        + " with Platform: "
                        + jsondata["platform.system"],
                        jsondata["compressionlevel"],
                    )
                    if jsondata["compressionlevel"] == "CompressionLevel.Max":
                        print(
                            colored(
                                "Since the uploader used very strong compression, decompression might take a long time",
                                "yellow",
                            )
                        )
                    if jsondata["version"] != "0.1":
                        print(
                            colored(
                                "This archive was not compressed with the same Share Archive Version as you are using for decompression. It might not decompress files that use compressors that have been added in later version. Check your extraction directory for still compressed files.",
                                "yellow",
                            )
                        )
                    # originalsize to compare after extraction
                    # originalSize=jsondata["originalsize"]
                try:
                    os.remove(filepath)
                except:
                    print(
                        "Infofile not removed (Info.json) from extraction folder")

            elif filename.endswith(".nncp"):
                strongFileList.append([filepath, filename])
            elif filename.endswith(".zpaq"):
                strongFileList.append([filepath, filename])
            else:
                p = multiprocessing.Process(
                    target=decompress, args=[filepath, filename]
                )
                processes.append(p)

    # memory saver : adjusting the number of concurrent processes (that use RAM)
    if memorySaverLvl == "Default":
        # all processes
        # start multiprocesses
        for process in processes:
            process.start()

        # join multiprocesses
        for process in processes:
            process.join()

        # split processes as to reduce memory usage (reduce number of concurrent processes)
        #  in half
    elif memorySaverLvl == "Low":

        #  in half
        processeslist0 = processes[: len(processes) // 2]
        processeslist1 = processes[len(processes) // 2:]

        # start multiprocesses first half
        for process in processeslist0:
            process.start()

        # join multiprocesses
        for process in processeslist0:
            process.join()

        # start multiprocesses second half
        for process in processeslist1:
            process.start()

        # join multiprocesses
        for process in processeslist1:
            process.join()
        #  in quarters
    elif memorySaverLvl == "Lower":

        #  in quarters
        processeslist0 = processes[: len(processes) // 2]
        processeslist1 = processes[len(processes) // 2:]
        processeslist00 = processes[: len(processeslist0) // 2]
        processeslist01 = processes[: len(processeslist0) // 2:]
        processeslist02 = processes[: len(processeslist1) // 2]
        processeslist03 = processes[: len(processeslist1) // 2:]

        # start multiprocesses first quarter
        for process in processeslist00:
            process.start()

        # join multiprocesses
        for process in processeslist00:
            process.join()

        # start multiprocesses second quarter
        for process in processeslist01:
            process.start()

        # join multiprocesses
        for process in processeslist01:
            process.join()

        # start multiprocesses third quarter
        for process in processeslist02:
            process.start()

        # join multiprocesses
        for process in processeslist02:
            process.join()

        # start multiprocesses fourth quarter
        for process in processeslist03:
            process.start()

        # join multiprocesses
        for process in processeslist03:
            process.join()

        # no parallelization at all, one after another (so for this file start one compressor and join (wait for finish), then start next compressor ...)
    elif memorySaverLvl == "Lowest":
        for process in processes:
            process.start()
            process.join()

        # decompress MAX compressed files after each other because of possible RAM requirements (like in compression)
    for list in strongFileList:
        decompress(list[0], list[1])

        ## SREP RESTORE ORIGINAL FILES ##

        # def restoresrep(filepath):
        #     try:
        #         subprocess.run(
        #             resource_path("")
        #             + "srep64 -d "
        #             + filepath,
        #             shell=True,
        #             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        #         )
        #     except:
        #         print("Could not restore srep")

        # def removesrep(filepath):
        #     try:
        #         if os.path.exists(filepath):
        #             os.remove(filepath)
        #         else:
        #             print("The preprocessed file " +
        #                   filepath + " does not exist")
        #     except:
        #         print("Could not remove preprocessed file " + filepath)

        # for subdir, dirs, files in os.walk(pathForExtractionFolder):
        #     for filename in files:
        #         filepath = subdir + os.sep + filename
        #         restoresrep(filepath)
        #         removesrep(filepath)

        # END OF RESTORE SREP FILES

        ## PRECOMP RESTORE ORIGINAL FILES ##

    def restoreprecompress(filepath):
        try:
            subprocess.run(
                resource_path("")
                + "precomp -r -o"+os.path.splitext(filepath)[0]+" "
                + filepath,
                shell=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except:
            print("Could not restoreprecompress")

    def removepreprocessed(filepath):
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
            else:
                print("The preprocessed file " +
                      filepath + " does not exist")
        except:
            print("Could not remove preprocessed file " + filepath)

    for subdir, dirs, files in os.walk(pathForExtractionFolder):
        for filename in files:
            filepath = subdir + os.sep + filename
            restoreprecompress(filepath)
            removepreprocessed(filepath)

        # END OF RESTORE PRECOMPRESS FILES

    print(
        colored("Program Execution Time (PET): ", "magenta")
        + str(round(time.time() - start_time, 2))
        + " seconds"
    )

    # DONE DECOMPRESSING

###################################################### The GUI #################################################


# Current Working Directiory for Input Selection Default Value (Starting Point)
currentWorkingDir = os.getcwd()

# PySimpleGUI Theme - Green on Black
sg.theme('Black')
sg.theme_text_color('#39ff14')
sg.theme_input_text_color('#39ff14')
sg.theme_element_text_color('#39ff14')
sg.theme_button_color('#39ff14')
sg.theme_background_color('Black')
sg.window_location = (0, 0)

# Layouts (individual Tabs)

# Compress Tab
compress_layout = [
    [sg.Text('Compression of a folder')],
    [sg.Text('Make sure to double click the Folders in the Input selection. You need to navigate into them for the GUI to use that path')],
    [sg.Text('Directory to compress'), sg.In(key='InputDirCompress'),
     sg.FolderBrowse(initial_folder=currentWorkingDir)],
    [sg.Text('Output Directory'), sg.In(
        key='OutputDirCompress'), sg.FolderBrowse(initial_folder=currentWorkingDir)],
    [sg.Text('Compression Level (stronger compression will greatly increase compression time):'), sg.Combo(['Fast', 'Default', 'Strong', 'MAX'],
                                                                                                           default_value='Default', key="CompressionLevel")],
    [sg.Text('Memory Saver (use this if you run out of memory. Will increase compression time):'), sg.Combo(['Default', 'Low', 'Lower', 'Lowest'],
                                                                                                            default_value='Default', key="MemorySaverLevel")],
    [sg.Text('Check the paths in the input fields before continuing')],
    [sg.Button('Compress', key="Compress"),
     sg.Button('Cancel', key="CancelCompress")]
]

# Decompress Tab
decompress_layout = [
    [sg.Text('Decompression of a Share File')],
    [sg.Text('Make sure to double click the Input File in the Input selection.')],
    [sg.Text('Compressed Share File'), sg.In(key='CompressedShareFile'), sg.FileBrowse(initial_folder=currentWorkingDir,
                                                                                       file_types=(("Share Files", "*.share"),))],
    [sg.Text('Output Directory'), sg.In(
        key='OutputDirectoryDecompress'), sg.FolderBrowse(initial_folder=currentWorkingDir)],
    [sg.Text('Memory Saver (use this if you run out of memory. Will increase decompression time):'), sg.Combo(['Default', 'Low', 'Lower', 'Lowest'],
                                                                                                              default_value='Default', key="MemorySaverLevelDecompress")],
    [sg.Text('Check the paths in the input fields before continuing')],
    [sg.Button('Decompress', key="Decompress"),
     sg.Button('Cancel', key="CancelDecompress")]
]

# About Tab
about_layout = [
    [sg.Text('Share Archiver v0.2')],
    [sg.Text('This is a little hobby test project')],
    [sg.Text('Files on sharing sites are often compressed once on the uploaders system, but downloaded and decompressed multiple times.')],
    [sg.Text('Share Archiver uses this circumstance by employing a costly compression process to reduce the file size for faster downloads,')],
    [sg.Text('while using high asymmetric compression algorithms with fast decompression speeds that allows for fast decompression as well.')],
    [sg.Text('Therefore optimizing this process by having the uploader invest more time&ressources once, for the profit of all subsequent downloaders.')],
    [sg.Text('There is also the MAX compression level included which uses strong symmetric compression algorithms')],
    [sg.Text('resulting in very long compression times and very long decompression times. This is meant for limit testing purposes.')],
    [sg.Text('This small application was made and will run on an Ubuntu 20.04.4 LTS')],
    [sg.Text('Use only for testing and experimenting around, no working guarantee')],
    [sg.Text('Philip Hofmann')],
]


# Main Layout with Tab Registers
layout = [
    [sg.Text('Share Archiver v 0.2', size=(38, 1), justification='center', font=("Helvetica", 16), relief=sg.RELIEF_RIDGE, k='-TEXT HEADING-', enable_events=True)]]
layout += [[sg.TabGroup([[sg.Tab('Decompress', decompress_layout), sg.Tab('Compress', compress_layout),
                        sg.Tab('About', about_layout), ]], key='-TAB GROUP-', expand_x=True, expand_y=True), ]]
layout[-1].append(sg.Sizegrip())
window = sg.Window('Share Archiver Tool', layout, grab_anywhere=False, margins=(0, 0), use_custom_titlebar=True, finalize=True
                   # scaling=2.0,
                   )
window.set_min_size(window.size)

# Event Loop to process events and get input values
while True:
    # Event
    event, values = window.read()
    print('GUI Event:' + event)

    # Check if Cancellation
    if event == sg.WIN_CLOSED or event == 'CancelCompress' or event == 'CancelDecompress':
        break

    # Compression Event
    if event == 'Compress':

        # Input Dir Provided?
        if not values['InputDirCompress']:
            print('You did not provide an Input Directory')
            sg.popup('No Input Directory supplied', keep_on_top=True)

        # Input Dir Path Check
        elif not os.path.exists(values['InputDirCompress']):
            print('The Input Directory Path check failed (os.path.exists)')
            sg.popup('Input Directory path check failed', keep_on_top=True)

        # Output Dir Provided?
        elif not values['OutputDirCompress']:
            print('You did not provide an Output Directory')
            sg.popup('No Output Directory supplied', keep_on_top=True)

        # Output Dir Path Check
        elif not os.path.exists(values['OutputDirCompress']):
            print('The Output Directory Path check failed (os.path.exists)')
            sg.popup('Output Directory path check failed', keep_on_top=True)

        elif os.path.exists(values['OutputDirCompress'] + ".share"):
            print(colored("ERROR: " + values['OutputDirCompress'] + ".share" + " archive already exists", "red")
                  )
            sg.popup('Output File exists already. Compression has been cancelled as to prevent overwriting an already existing share archive. Rerun this command with another archive name', keep_on_top=True)

        else:

            # Call Function
            print("Input Checks successful, calling compression function")
            print(values['InputDirCompress'])
            print(values['OutputDirCompress'])
            print(values['CompressionLevel'])
            print(values['MemorySaverLevel'])

            try:
                print("Start Compression")
                COMPRESS(values['InputDirCompress'],
                         values['OutputDirCompress'], values['CompressionLevel'], values['MemorySaverLevel'])
            except BaseException as error:
                sg.popup(error, keep_on_top=True)

            print('Done compressing')
            # createOlatZipFromFilesDirectly(
            #    values['InputDirectory'], values['ProcessScanCSV'], values['OutputDirectory'])

            # else:
            #    if not values['ProcessScanPDF']:
            #        print("Bob: Well you did not provide an Input Folder, but also not a scanned pdf. This is akward, since I dont know what to do. I think its safest if i just do nothing. Bleep.")
            #        sg.popup(
            #            'Cancel', '"No PDF or Input Directory supplied. Did you forget to check to take files directly? Beep Boop" - Bob, the artificial intelligence')
            #        raise SystemExit('Cancelling: no filename supplied')
            #    try:
            #        print("Bob: Since you provided an Scanned PDF, Im going to scan it and process it into a zip for Olat now. Beep Boop Biip.")
            #        complete_conversion(
            #            values['ProcessScanPDF'], values['ProcessScanCSV'], values['OutputDirectory'])
            #    except BaseException as error:
            #        sg.popup(error, keep_on_top=True)
            # print('Bob: See ya.')
            sg.popup('Done', keep_on_top=True)

    # Compression Event
    if event == 'Decompress':

        # File Input Provided?
        if not values['CompressedShareFile']:
            print(
                "No Share Input File provided .. did you double click the File in the input selection?")
            sg.popup('Cancel', 'No Compressed Input File supplied',
                     keep_on_top=True)

        # Input File Check
        elif not os.path.exists(values['CompressedShareFile']):
            print('The Compressed Input File Path check failed (os.path.exists)')
            sg.popup(
                'Input Compressed File path check failed', keep_on_top=True)

        elif not os.path.isfile(values['CompressedShareFile']) and not values['CompressedShareFile'].endswith(".share"):
            print('The Compressed Input File Path check failed (os.path.exists)')
            sg.popup(
                'Input Compressed File path check failed', keep_on_top=True)

        # Output Dir Provided?
        elif not values['OutputDirectoryDecompress']:
            print(
                "No Output Directory provided")
            sg.popup('No Directory Output supplied', keep_on_top=True)

        # Output Dir Path Check
        elif not os.path.exists(values['OutputDirectoryDecompress']):
            print('The Output Directory Path check failed (os.path.exists)')
            sg.popup(
                'Supplied Output Directory path check failed (path.exists)', keep_on_top=True)

        elif not os.path.isdir(values['OutputDirectoryDecompress']):
            print('The Output Directory IsDir check failed (os.path.isdor)')
            sg.popup(
                'Supplied Output Directory dir check failed (path.isdir)', keep_on_top=True)

        else:

            try:
                print("Decompressing")
                DECOMPRESS(values['CompressedShareFile'],
                           values['OutputDirectoryDecompress'],
                           values['MemorySaverLevelDecompress'])
            except BaseException as error:
                sg.popup(error, keep_on_top=True)
            print('Done decompressing')
            sg.popup('Done', keep_on_top=True)

window.close()
