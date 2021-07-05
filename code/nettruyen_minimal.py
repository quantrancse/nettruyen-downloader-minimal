import sys
import time
from concurrent.futures import ThreadPoolExecutor
from os import mkdir, path
from os.path import isdir

import requests
from bs4 import BeautifulSoup
from PyQt5 import uic
from PyQt5.QtCore import QObject, QRect, Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (QApplication, QDialog, QFileDialog, QLabel,
                             QLineEdit, QMainWindow, QMessageBox, QProgressBar,
                             QPushButton)

HEADERS = {
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
    'DNT': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Referer': 'http://www.nettruyenvip.com/',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9'
}


class MangaInfo():

    def __init__(self):
        self.manga_url = ''
        self.manga_name = ''
        self.chapter_name_list = []
        self.chapter_url_list = []
        self.save_path = ''
        self.list_of_download_chapter = []


class MessageBox(QMessageBox):

    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = path.abspath('.')

        return path.join(base_path, relative_path)

    def __init__(self, noti_text=''):
        super(MessageBox, self).__init__()
        self.setWindowTitle("Notification")
        self.setWindowIcon(QIcon((self.resource_path('icon.ico'))))
        self.setText(noti_text)
        self.exec_()


class WaitingDialog(QDialog):

    stop_signal = pyqtSignal()

    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = path.abspath('.')

        return path.join(base_path, relative_path)

    def initUI(self):
        # Dialog
        self.Dialog = QDialog()
        self.Dialog.resize(500, 200)
        self.Dialog.setWindowFlags(Qt.MSWindowsFixedSizeDialogHint)
        self.Dialog.setWindowIcon(QIcon((self.resource_path('icon.ico'))))
        font = QFont()
        font.setFamily('Verdana')
        self.Dialog.setFont(font)
        self.Dialog.setModal(True)
        self.Dialog.setWindowTitle('Please Wait ...')
        self.Dialog.setWindowFlags(Qt.WindowTitleHint)

        # Progress Bar
        self.progressBar = QProgressBar(self.Dialog)
        self.progressBar.setGeometry(QRect(30, 80, 451, 31))
        self.progressBar.setMaximum(100)
        self.progressBar.setValue(0)

        # Status
        self.label = QLabel(self.Dialog)
        self.label.setEnabled(True)
        self.label.setGeometry(QRect(30, 25, 441, 41))
        font = QFont()
        font.setFamily('Verdana')
        font.setPointSize(9)
        self.label.setFont(font)
        self.label.setText('Preparing ...')

        # Cancel/Close Button
        self.cancelButton = QPushButton('Cancel', self.Dialog)
        self.cancelButton.setGeometry(QRect(190, 140, 111, 31))
        self.cancelButton.clicked.connect(self.cancel)

    def run(self):
        self.Dialog.exec_()

    def cancel(self):
        self.stop_signal.emit()
        self.label.setText('Please wait ...')
        self.cancelButton.setEnabled(False)

    @pyqtSlot(int)
    def updateProgressBar(self, num):
        self.progressBar.setValue(num)

    @pyqtSlot(str)
    def updateChapterName(self, chapter_name):
        self.label.setText(chapter_name)

    @pyqtSlot(int)
    def setMaxProgessBarValue(self, max_value):
        self.progressBar.setMaximum(max_value)

    @pyqtSlot()
    def closeWhenDone(self):
        self.cancelButton.setText('Close')
        self.label.setText('Download Finished!')
        self.cancelButton.clicked.connect(self.Dialog.close)
        self.cancelButton.setEnabled(True)


class DownloadEngine(QThread):

    stop_signal = 0

    valueProgress = pyqtSignal(int)
    maxProgressValue = pyqtSignal(int)
    chapterName = pyqtSignal(str)
    isDone = pyqtSignal()

    def __init__(self, parent=None):
        super(DownloadEngine, self).__init__(parent)

    def setManga(self, manga):
        self.current_manga = manga
        self.image_formats = ['.jpg', '.jpeg', '.png', '.gif', '.tiff', '.bmp']
        self.stop_signal = 0
        self.error403_signal = 0
        self.error403_chapters = []

    def resetError403(self):
        self.error403_signal = 0
        self.error403_chapters = []

    @pyqtSlot()
    def stopDownload(self):
        self.stop_signal = 1

    def run(self):
        self.crawlChapterDataList()

    def crawlChapterDataList(self):
        chapter_list = []

        # Get each chapter info
        for index in self.current_manga.list_of_download_chapter:
            chapter_detail = {}
            chapter_detail['chapter_url'] = self.current_manga.chapter_url_list[index]
            chapter_detail['chapter_name'] = self.current_manga.chapter_name_list[index]
            if ':' in chapter_detail['chapter_name']:
                chapter_detail['chapter_name'] = chapter_detail['chapter_name'].split(':')[
                    0]
            chapter_list.append(chapter_detail)

        # Remove downloaded chapters | if not create directory
        chapter_list = [i_chapter for i_chapter in chapter_list if not isdir(
            self.current_manga.save_path + '/' + i_chapter['chapter_name'])]
        chapter_list = list(reversed(chapter_list))

        if chapter_list:
            # Set progress bar max value at 100%
            self.maxProgressValue.emit(len(chapter_list))

            # Create directory and start to download
            index = 0
            for chapter_data in chapter_list:

                if self.stop_signal:
                    break

                chapter_dir_path = self.current_manga.save_path + \
                    '/' + chapter_data['chapter_name']
                mkdir(chapter_dir_path.replace('\"', '').replace('\'', ''))
                chapter_data['chapter_dir_path'] = chapter_dir_path
                self.getChapterContents(chapter_data)
                index += 1
                self.valueProgress.emit(index)   # Update progress bar

        # Error 403 Dialog
        if self.error403_signal:
            chapters_403 = ', '.join(self.error403_chapters)
            MessageBox('Can not download some images: ' + chapters_403)
            self.resetError403()

        # Update download Finish Dialog
        self.isDone.emit()
        if chapter_list:
            self.valueProgress.emit(len(chapter_list))
        else:
            self.valueProgress.emit(100)
        print('Download Done')

    def getImageUrls(self, soup):
        contents = []

        for content_url in soup.find('div', class_='reading-detail box_doc').find_all('img'):
            if content_url not in contents:
                if any(img_fm in content_url['src'] for img_fm in self.image_formats):
                    img_url = content_url['src']
                elif content_url.has_attr('data-original'):
                    img_url = content_url['data-original']
                elif content_url.has_attr('data-cdn') and any(img_fm in content_url['data-cdn'] for img_fm in self.image_formats):
                    img_url = content_url['data-cdn']
                else:
                    img_url = content_url['src']
                contents.append(self.format_img_url(img_url))
        return contents

    def format_img_url(self, url):
        return url.replace('//', 'http://')

    def getImagePaths(self, chapter_dir_path, contents):
        img_path_list = []
        image_index = 1

        for img_url in contents:
            img_name = img_url.split('/')[-1]
            if any(img_fm in img_name[-4:] for img_fm in self.image_formats):
                img_path_name = chapter_dir_path + '/image_' + img_name
            else:
                img_path_name = chapter_dir_path + \
                    '/image_' + '{0:0=3d}'.format(image_index) + '.jpg'
            img_path_list.append(img_path_name)
            image_index += 1

        return img_path_list

    def getChapterContents(self, chapter_data):
        try:
            # Request chapter url
            request = requests.get(
                chapter_data['chapter_url'], headers=HEADERS, timeout=10)
            soup = BeautifulSoup(request.text, 'html.parser')

            # Get image url
            contents = self.getImageUrls(soup)

            # Get image name
            img_path_list = self.getImagePaths(
                chapter_data['chapter_dir_path'], contents)

            image_data_list = list(
                map(lambda x, y: (x, y), img_path_list, contents))

            # Update Dialog
            chapter_name = 'Downloading ' + \
                chapter_data['chapter_name'] + ' .....'
            print(chapter_name)
            self.chapterName.emit(chapter_name)

            # Threading for download each image
            with ThreadPoolExecutor(max_workers=20) as executor:
                executor.map(self.downloadImage, image_data_list)

            # Save error chapter
            if self.error403_signal:
                self.error403_chapters.append(chapter_data['chapter_name'])
        except:
            MessageBox('Error get chapter info. Please try again later.')
            print('Error Get Chapter Info: ' + chapter_data['chapter_url'])

        print('Finish ' + chapter_data['chapter_name'])

    def downloadImage(self, image_data_list):
        if not self.stop_signal:
            img_path_name, img_url = image_data_list

            # Limit download time of an image is 5 secs
            start = time.time()
            timeout = 10
            while True:
                try:
                    img_data = requests.get(
                        img_url, headers=HEADERS, timeout=10)
                    if img_data.status_code == 403:
                        self.error403_signal = 1
                    else:
                        with open(img_path_name, 'wb') as handler:
                            handler.write(img_data.content)
                    break
                except:
                    if time.time() - start > timeout:
                        MessageBox('Error download image: ' + img_path_name)
                        break
                    print('Retry: download image: ' + img_url)
                    time.sleep(1)
                    continue


class Ui(QMainWindow):

    start_download = pyqtSignal(str, str, str)

    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = path.abspath('.')

        return path.join(base_path, relative_path)

    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi(self.resource_path('nettruyen_minimal.ui'), self)
        self.setWindowIcon(QIcon((self.resource_path('icon.ico'))))

        self.bridge = Bridge()

        self.mangaUrlEdit = self.findChild(QLineEdit, 'mangaUrlEdit')
        self.fromChapterEdit = self.findChild(QLineEdit, 'fromChapterEdit')
        self.toChapterEdit = self.findChild(QLineEdit, 'toChapterEdit')

        self.downloadButton = self.findChild(QPushButton, 'downloadButton')
        self.downloadButton.clicked.connect(self.downloadButtonPress)

        self.downloadAllButton = self.findChild(
            QPushButton, 'downloadAllButton')
        self.downloadAllButton.clicked.connect(self.downloadAllButtonPress)

        self.start_download.connect(self.bridge.startDownload)

        self.show()

    def downloadButtonPress(self):
        self.start_download.emit(self.mangaUrlEdit.text(
        ), self.fromChapterEdit.text(), self.toChapterEdit.text())

    def downloadAllButtonPress(self):
        self.start_download.emit(
            self.mangaUrlEdit.text(), 'start_chapter', 'end_chapter')


class Bridge(QObject):

    current_manga = MangaInfo()

    @pyqtSlot(str, str, str)
    def startDownload(self, manga_url, from_chapter_input, to_chapter_input):
        self.manga_url = manga_url
        self.from_chapter_input = from_chapter_input
        self.to_chapter_input = to_chapter_input
        self.downloadChapter()

    def downloadChapter(self):
        if self.checkValidUrl() and self.getChapterInput():
            get_path = str(QFileDialog.getExistingDirectory(
                None, "Select Save Directory"))

            if get_path:
                if isdir(get_path):
                    manga_save_path = get_path + '/' + \
                        self.current_manga.manga_name
                    manga_save_path = manga_save_path.replace(
                        '\"', '').replace('\'', '')
                    if not isdir(manga_save_path):
                        mkdir(manga_save_path)

                    self.current_manga.save_path = manga_save_path

                    engine = DownloadEngine(self)
                    engine.setManga(self.current_manga)
                    dialog = WaitingDialog()
                    dialog.initUI()

                    engine.valueProgress.connect(dialog.updateProgressBar)
                    engine.maxProgressValue.connect(
                        dialog.setMaxProgessBarValue)
                    engine.chapterName.connect(dialog.updateChapterName)
                    engine.isDone.connect(dialog.closeWhenDone)
                    dialog.stop_signal.connect(engine.stopDownload)

                    engine.start()
                    dialog.run()
                else:
                    MessageBox("Invalid Save Folder. Please try again.")
        else:
            return

    def checkValidUrl(self):
        current_manga_url = self.manga_url

        if not any(substr in current_manga_url for substr in ['nhattruyenhay.com/truyen-tranh/', 'nettruyenvip.com/truyen-tranh/']):
            MessageBox("Invalid manga url. Please try again.")
            return False
        else:
            try:
                request = requests.get(
                    current_manga_url, headers=HEADERS, timeout=5)
                soup = BeautifulSoup(request.text, 'html.parser')
                if not soup.find('div', id='nt_listchapter'):
                    MessageBox("Invalid manga url. Please try again.")
                    return False
                else:
                    self.current_manga.manga_url = str(current_manga_url)
                    self.crawlMangaHomePage()
                    return True
            except requests.ConnectionError:
                MessageBox("Cannot get manga url.")

    def crawlMangaHomePage(self):
        try:
            print('Start crawling ---------', self.current_manga.manga_url)
            request = requests.get(
                self.current_manga.manga_url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(request.text, 'html.parser')

            self.current_manga.manga_name = soup.find(
                'h1', class_='title-detail').text

            self.current_manga.chapter_name_list = [
                i.find('a').text for i in soup.find_all('div', class_='chapter')]

            chapter_url_list = []
            for chapter in soup.find('div', id='nt_listchapter').find('ul').find_all('a'):
                chapter_url_list.append(chapter['href'])
            self.current_manga.chapter_url_list = chapter_url_list

        except:
            MessageBox('Error getting manga page. Please try again.')
            print('exception crawling manga !')

    def getChapterIndex(self, chapter_input):
        if chapter_input == 'start_chapter':
            return 0
        elif chapter_input == 'end_chapter':
            return len(self.current_manga.chapter_name_list) - 1
        else:
            for chapter in self.current_manga.chapter_name_list:
                chapter_name = chapter.split()[1]
                if ':' in chapter_name:
                    chapter_name = chapter_name[:-1]
                if chapter_input == chapter_name:
                    return self.current_manga.chapter_name_list.index(
                        chapter)
            return None

    def getChapterInput(self):
        from_chapter_index = self.getChapterIndex(
            self.from_chapter_input)
        to_chapter_index = self.getChapterIndex(self.to_chapter_input)

        if from_chapter_index is not None and to_chapter_index is not None:
            if from_chapter_index > to_chapter_index:
                from_chapter_index, to_chapter_index = to_chapter_index, from_chapter_index
            self.current_manga.list_of_download_chapter = list(
                range(from_chapter_index, to_chapter_index + 1))
            return True
        else:
            MessageBox(
                "Invalid Manga Chapter Input. Please try again.")
            return False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Ui()
    window.setWindowTitle('Nettruyen Downloader')
    app.exec_()
