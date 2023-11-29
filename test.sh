#!/bin/bash
r=("asdf" "bar")
res=$(node -e "console.log(process.argv)" ${r[@]})
echo $res