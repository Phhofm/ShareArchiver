Lossless Data Compression with Neural Networks
==============================================

1) Overview
-----------

NNCP is an experimental lossless data compressor using Neural
Networks. Two models are available: Transformer (slower but best
ratio) and LSTM (faster). A text preprocessor and tokenizer can
optionally be enabled. More information is available at
https://bellard.org/nncp .

Thanks to LibNC, it supports both the GPU (NVIDIA CUDA version 11.x
required with an Ampere GPU) and CPU. For an acceptable speed with
large models, a GPU is required.

Use './test.sh all' to do a regression test.

2) Compilation
--------------

A Linux system is assumed. Just type 'make' to compile the program. A
binary DLL of the LibNC library is included in the archive. Windows
cross-compilation from Linux is supported.

5) Current best models for enwik8/enwik9
----------------------------------------

enwik8:

  ./nncp --cuda --profile enwik8 --preprocess 4096,512 c enwik8 out.bin
  
  Result: 14969569 bytes (2.36 kB/s)

enwik9:

  ./nncp --cuda --profile enwik9 --preprocess 16384,512 c enwik9 out.bin

  Result: 108378032 (4.74 kB/s)

Decompression:

  ./nncp --cuda d out.bin out.txt

  Decompression has a similar speed than compression.

Test system: Xeon E3-1230 @ 3.5 GHz + RTX 3090 NVIDIA GPU

Memory usage: CPU: 1 GB, GPU: 5 GB

6) Licence
----------

The source code is released under the MIT licence.

The LibNC library is provided in binary form and can be freely redistributed.
