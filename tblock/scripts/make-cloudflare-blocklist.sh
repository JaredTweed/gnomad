#!/bin/sh

__retrieve_lists()
{
    for x in a b c d e f g h i j k l m n o p q r s t u v w x y z 0 1 2 3 4 5 6 7 8 9; do 
        curl "https://framagit.org/dCF/deCloudflare/-/raw/master/cloudflare_users/domains/TXT/cloudflare_$x.txt" >> $1; 
    done
}

__help()
{
    echo "$0 <output>"
}

case $1 in
    "-"*)
        __help
        ;;
    "")
        __help
        ;;
    *)
        __retrieve_lists $1
        ;;
esac
