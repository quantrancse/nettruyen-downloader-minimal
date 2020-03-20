import sys
from os import mkdir
from os.path import isdir

from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5 import uic
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import (
    QApplication, QFileDialog, QLineEdit, QMainWindow, QPushButton)

import requests
from bs4 import BeautifulSoup
from download_engine import DownloadEngine
from manga_info import MangaInfo
from message_box import MessageBox
from waiting_dialog import WaitingDialog


class Ui(QMainWindow):

    start_download = pyqtSignal(str, str, str)

    def __init__(self, ui_file):
        super(Ui, self).__init__()
        uic.loadUi(ui_file, self)

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

        if not any(substr in current_manga_url for substr in ['nhattruyen.com/truyen-tranh/', 'nettruyen.com/truyen-tranh/']):
            MessageBox("Invalid manga url. Please try again.")
            return False
        else:
            request = requests.get(current_manga_url, timeout=5)
            soup = BeautifulSoup(request.text, 'html.parser')
            if not soup.find('div', id='nt_listchapter'):
                MessageBox("Invalid manga url. Please try again.")
                return False
            else:
                self.current_manga.manga_url = str(current_manga_url)
                self.crawlMangaHomePage()
                return True

    def crawlMangaHomePage(self):
        try:
            print('Start crawling ---------', self.current_manga.manga_url)
            request = requests.get(self.current_manga.manga_url,  timeout=10)
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
    appctxt = ApplicationContext()
    ui_file = appctxt.get_resource('nettruyen_minimal.ui')
    window = Ui(ui_file)
    exit_code = appctxt.app.exec_()
    sys.exit(exit_code)
