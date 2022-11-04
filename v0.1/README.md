# Share Archiver v0.1

Share Archiver’s vision is to achieve faster downloads for all by improving online file sharing through small archive size with fast decompression.

Since files shared online are only once compressed and uploaded by the uploader, but downloaded and decompressed numerous times. The focus was therefore on achieving smallest archive size, which leads to faster downloads because less data transmitted overall, while still having fast decompression speeds to still be practical for the downloaders of the uploaded share archive.
It's approach is to only use strong asymmetric compressors with fast decompression speeds, and benchmarking each file for smallest archive size for compressor selection.

The current version 0.1 can make use of these great compressors: Zlib, Balz, LZMA (XZ), GZip, Zstandard, PPmd, LZ4, Brotli, LZHAM, ZOPFLI, Lzturbo, GLZA, Balz, BSC, CSArc, NNCP, ZPAQ
Shoutout to the developers of these great compressors, they did such just an amazing job and invested a lot of time for the community to profit thereof and make use of it.

You will find the executables in the executable folder with both singlefile, folder versions and the bare python file in the python folder. I recommend the Ubuntu20 Single File Flavor, but if you are still using Ubunt18 then of course the Ubuntu18 Single File Flavor.

In the notes folder there are more thoughts which were generated during the development/tryout of this version.

In the corpus folder is are the files from the maximumcompression corpus I had used as a testset to test the compression and compare also archive sizes with other archivers.

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

-----  

## Additional info  
### Quick Size Benchmark Comparison v0.1  
The default profile has been used for all of these  

 11735040 maximumcompressioncorpus.share  
 12177048 maximumcompressioncorpus.7z  
 12403504 maximumcompressioncorpus.tar.xz  
 12412975 maximumcompressioncorpus.tar.lzma  
 12412988 maximumcompressioncorpus.tar.lz  
 12523696 maximumcompressioncorpus.tar.7z  
 12654720 maximumcompressioncorpus.exe  
 13610427 maximumcompressioncorpus.tar.bz2  
 14405261 maximumcompressioncorpus.zip  
 14405261 maximumcompressioncorpus.cbz  
 15095465 maximumcompressioncorpus.tar.gz  
 15102263 maximumcompressioncorpus.war  
 15102263 maximumcompressioncorpus.jar  
 15102263 maximumcompressioncorpus.ear  
 15102263 maximumcompressioncorpus.crx  
 15102263 maximumcompressioncorpus.apk  
 15311263 maximumcompressioncorpus.tar.zst  
 20907094 maximumcompressioncorpus.tar.lz4  
 21334955 maximumcompressioncorpus.tar.lzo  
 21427739 maximumcompressioncorpus.tar.Z  
 53135336 maximumcompressioncorpus.ar  
 53136148 maximumcompressioncorpus.cpio  
 53144064 maximumcompressioncorpus.tar  
 53522432 maximumcompressioncorpus.iso  

Times Share Archiver:

Compression, Fast:  
Original Size: 53134726  
Archive Size: 11755520  
Compression Ratio: 4.5199809110953835  
Program Execution Time (PET): 11.13 seconds  
Decompression:  
Program Execution Time (PET): 0.36 seconds  

Compression, Default:  
Original Size: 53134726  
Archive Size: 11735040  
Compression Ratio: 4.527869184936736  
Program Execution Time (PET): 156.91 seconds  
Decompression:  
Program Execution Time (PET): 0.34 seconds  

Compression, Strong:  
Original Size: 53134726  
Archive Size: 11376640  
Compression Ratio: 4.670511328476597  
Program Execution Time (PET): 254.39 seconds  
Decompression:  
Program Execution Time (PET): 0.31 seconds  

Compression, Max:  
Original Size: 53134726  
Archive Size: 11100160  
Compression Ratio: 4.786843252709871  
Program Execution Time (PET): 16464.23 seconds  
Decompression:  
Program Execution Time (PET): 6479.34 seconds  

### Even more info concerning v0.1, pdf as images displayed here
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0001.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0002.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0003.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0004.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0005.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0006.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0007.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0008.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0009.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0010.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0011.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0012.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0013.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0014.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0015.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0016.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0017.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0018.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0019.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0020.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0021.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0022.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0023.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0024.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0025.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0026.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0027.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0028.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0029.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0030.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0031.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0032.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0033.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0034.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0035.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0036.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0037.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0038.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0039.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0040.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0041.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0042.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0043.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0044.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0045.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0046.jpg?raw=true)
![PDFPage](https://github.com/Phhofm/ShareArchiver/blob/main/v0.1/notes/pdf/0047.jpg?raw=true)

