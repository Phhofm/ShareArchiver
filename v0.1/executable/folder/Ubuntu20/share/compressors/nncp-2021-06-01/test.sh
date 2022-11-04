#!/bin/sh
set -e

args=""

if [ "$1" = "-T" -o "$1" = "-batch_size" ] ; then
    args="$1 $2"
    shift
    shift
fi

prog="$1"
file="$2"
if [ '!' '(' "$prog" = "all" -o "$prog" = "nncp2" -o "$prog" = "nncp" -o \
         "$prog" = "nncp_lstm" ')' ] ; then
    echo "Regression tests"
    echo ""
    echo "usage: test.sh [-T n] all|nncp2|nncp|nncp_lstm [infile]"
    exit 1
fi

hash="n"
if [ "$file" = "" ] ; then
    file="test/enwik4"
    hash="y"
fi

if [ $prog = "nncp_lstm" -o $prog = "all" ] ; then

    ./nncp -p lstm $args c "$file" /tmp/out-nncp_lstm.bin
    if [ $hash = "y" ] ; then
        if [ -f test/out-nncp_lstm.hash ] ; then
            sha256sum -c test/out-nncp_lstm.hash
        else
            sha256sum /tmp/out-nncp_lstm.bin > test/out-nncp_lstm.hash
        fi
    fi
    ./nncp $args d /tmp/out-nncp_lstm.bin /tmp/out.txt
    cmp /tmp/out.txt "$file"

fi

if [ $prog = "nncp" -o $prog = "all" ] ; then

    ./nncp $args c "$file" /tmp/out-nncp.bin
    if [ $hash = "y" ] ; then
        if [ -f test/out-nncp.hash ] ; then
            sha256sum -c test/out-nncp.hash
        else
            sha256sum /tmp/out-nncp.bin > test/out-nncp.hash
        fi
    fi
    ./nncp $args d /tmp/out-nncp.bin /tmp/out.txt
    cmp /tmp/out.txt "$file"

fi

if [ $prog = "nncp2" -o $prog = "all" ] ; then

    ./nncp $args --bf16 1 --d_pos 64 --sparse_grad 1 --preprocess 512,8 c "$file" /tmp/out-nncp2.bin
    
    if [ $hash = "y" ] ; then
        if [ -f test/out-nncp2.hash ] ; then
            sha256sum -c test/out-nncp2.hash
        else
            sha256sum /tmp/out-nncp2.bin > test/out-nncp2.hash
        fi
    fi

    ./nncp $args d /tmp/out-nncp2.bin /tmp/out.txt
    cmp /tmp/out.txt "$file"
fi
