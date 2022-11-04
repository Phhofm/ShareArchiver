# Share Archiver v0.1

\_Flavor: SingleBinary20

Share Archiver’s vision is to achieve faster downloads for all by improving online file sharing through small archive size with fast decompression.

Since files shared online are only once compressed and uploaded by the uploader, but downloaded and decompressed numerous times. The focus was therefore on achieving smallest archive size, which leads to faster downloads because less data transmitted overall, while still having fast decompression speeds to still be practical for the downloaders of the uploaded share archive.
It's approach is to only use strong asymmetric compressors with fast decompression speeds, and benchmarking each file for smallest archive size.

The current version 0.1 can make use of these great compressors: Zlib, Balz, LZMA (XZ), GZip, Zstandard, PPmd, LZ4, Brotli, LZHAM, ZOPFLI, Lzturbo, GLZA, Balz, BSC, CSArc, NNCP, ZPAQ
Shoutout to the developers of these great compressors, they did such just an amazing job and invested a lot of time for the community to profit thereof and make use of it.

This is the SingleBinary20 version, generated with pyinstaller on Ubuntu20. Since pyinstaller does not generate executables compatible with older systems, there also exists the SingleBinary18 Flavor, generated on a Ubuntu18. Additionaly, I provide the FolderBinary Flavors (18 and 20 again), where some of these compressors are provided and used from the external 'compressors' folder. These additional flavors enables you to build them for yourself on your system (run make against any of these compressors that might not run on your system), and might be necessary since this is the very first, and so far only personally tested, version of it.

## Usage

This application will compress an input folder and decompress a share archive to an output folder.
For the argument inputs, absolute paths as well as relatives paths are accepted.
There is a help menu integrated, which will show by running share -h

As a simple example, to compress, run
share compress /path/to/input/folder /path/to/output/filename

So the first argument is a folder path, the second argument is a path with the filename. It will create a .share file with the provided filename, therefore ./silesia will generate a silesia.share file

To decompress, run
share decompress /path/to/input/archive.share /path/to/output/folder

The first argument is the share archive (dont forget the .share) and the second is the extraction path, it will generate a folder with the archive filename. So "share decompress ../input/silesia.share ../output" will generate a ../output/silesia folder with the extracted files in it.

It this folder to be generated already exists (a subfolder in the output path provided with the same name as the archive), share archiver will quit and show a prompting to resolve this conflict manually. This is simply because I did not want share to automatically overwrite any already extracted files - share assumes that this specific archive has already been extracted to this output folder path previously if this directory is already present. To resolve it, create a intermediate output folder and include it in the output path, or remove said folder with its content.

## Profiles

There are also profiles integrated. Using those limits or extends the number of compressors used for one compression.

Fast (0)
Default (1)
Strong (2)
Max (3)

which can be activated by using the levels (some examples):

share -lvl 0 compress /home/phhofm/Dokumente/silesia /home/phhofm/Dokumente/output/silesia_fast
share -v -lvl 2 -ms 1 compress ../silesia ../output/silesia_strong
share decompress ../output/silesia_strong.share ../extract
share -v -lvl 3 -ms 1 compress ../silesia ../output/silesia_max

These profiles will mainly affect compression speed and compression ratio, with the exception of the Max profile:

The Max profile shall not be used for online file sharing, since it will make use of compressors with long decompression times, its goal is only small archive size, and can be used for personal interests.

Info for the arguments should also be availabe by running share -h

Thanks for trying out Share Archiver :D
Philip Hofmann
