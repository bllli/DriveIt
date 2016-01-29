from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QThread, pyqtSignal
from window import Ui_MainWindow
from base import SharedBase
import sys
import time


class MyMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MyMainWindow, self).__init__()
        self.setupUi(self)
        self.pushButton.clicked.connect(self.do)

    def do(self):
        try:
            self.user_input_url = self.lineEdit.text()
            self.pushButton.setDisabled(True)
            self.base = SharedBase(self.user_input_url)
            self.site_name = self.base.get_site_name()
            self.work = WorkingThread(self.site_name, self.user_input_url)
            self.work.status_report_signal.connect(self.status_receive_signal)
            self.work.progress_report_signal.connect(self.progress_receive_signal)
            self.work.start()
        except NameError as e:
            self.statusBar().showMessage('Website %s illegal or not supported' % e)
            self.pushButton.setDisabled(False)

    def status_receive_signal(self, text):
        self.statusBar().showMessage(text)

    def progress_receive_signal(self, progress):
        self.progressBar.setProperty("value", progress)


class WorkingThread(QThread):
    status_report_signal = pyqtSignal(str)
    progress_report_signal = pyqtSignal(float)

    def __init__(self, site_name, url):
        super(WorkingThread, self).__init__()
        self.site_name = site_name
        self.user_input_url = url

    def run(self):
        if self.site_name == 'dm5':
            from dm5 import DM5 as SiteClass
        elif self.site_name == 'ck101':
            from ck101 import Ck101 as SiteClass
        self.website_object = SiteClass(self.user_input_url)
        self.comic_name = self.website_object.get_name()
        self.ref_box = self.website_object.get_chapter_info()
        self.status_report_signal.emit('%s, total %d chapters detected.' % (self.comic_name, max(self.ref_box.keys())))
        self.main_loop(self.ref_box)

    def main_loop(self, refer_box, is_volume=False):
        total_parents = max(refer_box.keys())
        if is_volume is True:
            parent_str = 'Volume'
        else:
            parent_str = 'Chapter'
        for parent in range(1, total_parents + 1):
            if parent in refer_box.keys():
                cid = refer_box[parent]
                for page in range(1, self.website_object.get_page_info(cid) + 1):
                    link = self.website_object.get_image_link(cid, page)
                    try:
                        self.website_object.down(self.comic_name, cid, link, parent, page, is_volume)
                        self.status_report_signal.emit(
                                '%s %d page %d has been downloaded successfully' % (parent_str, parent, page))
                        progress = page / self.website_object.get_page_info(cid)
                        self.progress_report_signal.emit(progress * 100)
                    except:
                        self.status_report_signal.emit(
                                'Error occurred when downloading %s %d, Page %d.' % (parent_str, parent, page))
            else:
                self.status_report_signal.emit('Chapter %d cannot be found.' % parent)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyMainWindow()
    window.show()
    sys.exit(app.exec_())