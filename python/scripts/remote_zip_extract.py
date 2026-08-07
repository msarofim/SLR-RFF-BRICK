#!/usr/bin/env python3
"""List / selectively extract members of a remote zip via HTTP range requests.

Usage:
  remote_zip_extract.py URL --list [pattern]
  remote_zip_extract.py URL --extract pattern outdir
"""
import fnmatch
import io
import sys
import urllib.request
import zipfile


class HttpRangeFile(io.RawIOBase):
    def __init__(self, url):
        self.url = url
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req) as r:
            self.length = int(r.headers["Content-Length"])
            if r.headers.get("Accept-Ranges", "none").lower() != "bytes":
                # some servers omit the header but still honor ranges; try anyway
                pass
        self.pos = 0
        self.nreq = 0
        self.nbytes = 0

    def seek(self, offset, whence=0):
        if whence == 0:
            self.pos = offset
        elif whence == 1:
            self.pos += offset
        elif whence == 2:
            self.pos = self.length + offset
        return self.pos

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def read(self, n=-1):
        if n == -1:
            n = self.length - self.pos
        if n <= 0 or self.pos >= self.length:
            return b""
        end = min(self.pos + n, self.length) - 1
        req = urllib.request.Request(self.url)
        req.add_header("Range", f"bytes={self.pos}-{end}")
        with urllib.request.urlopen(req) as r:
            data = r.read()
        self.pos += len(data)
        self.nreq += 1
        self.nbytes += len(data)
        return data

    def readinto(self, b):
        data = self.read(len(b))
        b[: len(data)] = data
        return len(data)


def main():
    url = sys.argv[1]
    f = HttpRangeFile(url)
    bf = io.BufferedReader(f, buffer_size=512 * 1024)
    zf = zipfile.ZipFile(bf)
    if sys.argv[2] == "--list":
        pat = sys.argv[3] if len(sys.argv) > 3 else "*"
        for info in zf.infolist():
            if fnmatch.fnmatch(info.filename, pat):
                print(f"{info.file_size:>12}  {info.filename}")
    elif sys.argv[2] == "--extract":
        pat, outdir = sys.argv[3], sys.argv[4]
        for info in zf.infolist():
            if fnmatch.fnmatch(info.filename, pat) and not info.is_dir():
                zf.extract(info, outdir)
                print(f"extracted {info.filename} ({info.file_size} B)")
    print(f"[transfer: {f.nreq} range requests, {f.nbytes/1e6:.2f} MB]",
          file=sys.stderr)


if __name__ == "__main__":
    main()
