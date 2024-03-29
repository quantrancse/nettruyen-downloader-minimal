![Python Version][python-shield]
![PyQt5 Version][pyqt5-shield]
[![MIT License][license-shield]][license-url]



<!-- PROJECT LOGO -->
<br />
<p align="center">
    <img src="images/screenshot.png" alt="Logo" "></img>

  <h2 align="center">NetTruyen Downloader Minimal</h2>

  <p align="center">
    Minimal version without QML of <a href=https://github.com/quantrancse/nettruyen-downloader>Nettruyen Downloader</a>
    <br />
    <br />
  </p>
</p>

<!-- ABOUT -->
## About
[Update: 06-07-2021] This tool still working if nettruyen change domain.

[Other] I've found a Tampermonkey script that works on different manga sites: https://github.com/lelinhtinh/Userscript/tree/master/manga_comic_downloader

Thanks to the author and use it by your own way.

---

For more infomation about the project please read in [Nettruyen Downloader](https://github.com/quantrancse/nettruyen-downloader).

<!-- Download -->
## Download

**Windows**: [nettruyen_minimal.exe ~ 35MB](https://rebrand.ly/nettruyen_minimal)

##### Recommend Manga Viewer

* I have found a good image viewer application that perfectly suited for reading manga - [QuickViewer](https://kanryu.github.io/quickviewer/)
              
<!-- Build Project -->
## Build Project

### Prerequisites

* python 3.9.7
* PyQt5
```sh
pip install pyqt5
```
* pyinstaller
```sh
pip install bs4 requests pyqt5 pyinstaller
```
* Some IDE if needed: Qt Designer

### Installation

* Clone the repo
```sh
git clone https://github.com/quantrancse/nettruyen-downloader-minimal.git
```
* Modify the source code
* Build .exe file
```sh
pyinstaller ./nettruyen_minimal.spec
```
  
<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to be learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request



<!-- LICENSE -->
## License

Distributed under the MIT License. See [LICENSE][license-url] for more information.

<!-- CONTACT -->
## Contact

* **Author** - [@quantrancse](https://www.facebook.com/quantrancse)

<!-- ACKNOWLEDGEMENTS -->
## Acknowledgements
* [PyQt5 tutorial](https://build-system.fman.io/pyqt5-tutorial)
* [Qt Documentation](https://doc.qt.io/)

<!-- MARKDOWN LINKS & IMAGES -->
[python-shield]: https://img.shields.io/badge/python-3.9.6-brightgreen?style=flat-square
[pyqt5-shield]: https://img.shields.io/badge/PyQt5-5.14.1-blue?style=flat-square
[license-shield]: https://img.shields.io/github/license/quantrancse/nettruyen-downloader?style=flat-square
[license-url]: https://github.com/quantrancse/nettruyen-downloader-minimal/blob/master/LICENSE
