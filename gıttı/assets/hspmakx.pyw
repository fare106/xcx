import sqlite3
from PIL import Image, ImageDraw, ImageFont
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QColor, QMovie
from PyQt5 import QtWidgets, uic, QtCore, QtGui
from PyQt5.QtWidgets import QGraphicsOpacityEffect, QGraphicsDropShadowEffect, QMainWindow, QLabel, QPushButton, QApplication, QInputDialog
import sys
import locale
import datetime
import win32com.client
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QGuiApplication

# Tarih adaptörü ekle
def adapt_date(date):
    return date.isoformat()

def convert_date(bytestring):
    return datetime.date.fromisoformat(bytestring.decode("utf-8"))

sqlite3.register_adapter(datetime.date, adapt_date)
sqlite3.register_converter("DATE", convert_date)

QGuiApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QGuiApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # Veritabanını başlat
        self.init_database()

        try:
            # UI dosyasını yükle
            uic.loadUi(r"G:\\PROGRAM\\HESAPMAKINESI\\HSPMAK1.ui", self)
        except Exception as e:
            print(f"Error loading UI file: {e}")

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        self.setupGif()
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setColor(QColor(255, 255, 255))
        self.shadow.setOffset(0, 0)
        self.setGraphicsEffect(self.shadow)
        self.selected_value = None  # Seçilen değeri saklamak için
        self.pending_operator = None  # Bekleyen operatörü saklamak için
        # Ekran çözünürlüğüne göre pencerenin konumunu ayarla
        screen_geometry = QtWidgets.QDesktopWidget().availableGeometry()
        x = 1200
        y = 90
        self.move(x, y)

        self.setWindowTitle('Draggable QListView Example')

        self.show()

        self.model = QStandardItemModel()
        self.listView.setModel(self.model)

        # Çoklu seçim modunu etkinleştir
        self.listView.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        # Çift tıklama olayını bağla
        self.listView.doubleClicked.connect(self.edit_item)

        self.listView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.current_result = 0.0
        self.first_operation = True

        self.current_index = 0

        self.dragging = False
        self.drag_start_position = QtCore.QPoint()

        try:
            self.pushButton_1.clicked.connect(lambda: self.calculate_result("+"))
            self.pushButton_2.clicked.connect(lambda: self.add_operator("+"))
            self.pushButton_3.clicked.connect(lambda: self.add_operator("-"))
            self.pushButton_4.clicked.connect(lambda: self.add_operator("*"))
            self.pushButton_5.clicked.connect(lambda: self.add_operator("/"))
            self.pushButton_6.clicked.connect(self.delete_selected_items)
            self.pushButton_6.installEventFilter(self)
            self.pushButton_23.clicked.connect(self.load_all_today_records)
            self.pushButton_77.clicked.connect(self.load_last_record)
            self.pushButton_7.clicked.connect(self.get_records_by_date)
            self.pushButton_8.clicked.connect(lambda: self.showMinimized())
            self.pushButton_10.clicked.connect(self.close)
        

            # Ekran çözünürlüğüne göre pencerenin konumunu ayarla
           

          

            self.model = QStandardItemModel()
            self.listView.setModel(self.model)

            # Çoklu seçim modunu etkinleştir
            self.listView.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

            # ListView'de tıklama olayını bağla
            self.listView.clicked.connect(self.list_view_clicked)

            # Eşittir butonuna tıklama olayını bağla
            self.pushButton_equals.clicked.connect(self.calculate_from_selection)


        except AttributeError as e:
            print(f"Button connection error: {e}")

        try:
            self.textEdit.installEventFilter(self)
        except AttributeError as e:
            print(f"textEdit error: {e}")

        self.installEventFilter(self)

    def setupGif(self):
        try:
            self.movie1 = QMovie(r'G:\\PROGRAM\\HESAPMAKINESI\\gıff-5.gif')
            self.label_9.setMovie(self.movie1)
            self.movie1.setScaledSize(self.label_9.size())
            self.movie1.start()

            self.movie2 = QMovie(r'G:\\PROGRAM\\HESAPMAKINESI\\gıff-66.gif')
            self.label_10.setMovie(self.movie2)
            self.movie2.setScaledSize(self.label_10.size())
            self.movie2.start()
        except Exception as e:
            print(f"Error setting up GIFs: {e}")

    

    def eventFilter(self, source, event):
        try:
            if event.type() == QtCore.QEvent.KeyPress:
                if event.key() == QtCore.Qt.Key_C and event.modifiers() == QtCore.Qt.ControlModifier:
                    self.copy_selected_items()
                    return True
                if event.key() in [QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return] and source is self.textEdit:
                    self.add_to_listview()
                    return True
            elif event.type() == QtCore.QEvent.MouseButtonDblClick:
                if source == self.pushButton_6:
                    self.clear_listview()
                    self.textEdit.setFocus()
                    return True
            elif event.type() == QtCore.QEvent.MouseMove:
                if self.rect().contains(self.mapFromGlobal(event.globalPos())):
                    self.textEdit.setFocus()
        except Exception as e:
            print(f"Event filter error: {e}")
        return super().eventFilter(source, event)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.dragging = True
            self.drag_start_position = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(event.globalPos() - self.drag_start_position)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.dragging = False

    def copy_selected_items(self):
        try:
            selected_indexes = self.listView.selectedIndexes()
            if not selected_indexes:
                return
            selected_texts = "\n".join([self.model.itemFromIndex(index).text().strip() for index in selected_indexes])
            clipboard = QApplication.clipboard()
            clipboard.setText(selected_texts)
        except Exception as e:
            print(f"Error copying items: {e}")

    def format_number(self, number):
        try:
            formatted_number = "{:,.3f}".format(number).replace(",", "X").replace(".", ",").replace("X", ".")
            return formatted_number.rstrip('0').rstrip(',')
        except Exception as e:
            print(f"Number formatting error: {e}")
            return str(number)

    def calculate_result(self, operator):
        try:
            self.current_result = 0.0
            new_values = []
            for i in range(self.model.rowCount()):
                item = self.model.item(i).text().strip()
                try:
                    if item.strip():
                        value = float(item.split()[-1].replace(".", "").replace(",", "."))
                        new_values.append(value)
                    else:
                        new_values = []
                except (IndexError, ValueError):
                    continue
            if not new_values:
                return
            self.current_result = new_values[0]
            for value in new_values[1:]:
                if operator == '+':
                    self.current_result += value
                elif operator == '-':
                    self.current_result -= value
                elif operator == '*':
                    self.current_result *= value
                elif operator == '/':
                    if value != 0:
                        self.current_result /= value
                    else:
                        self.model.appendRow(QStandardItem("Bölme Hatası: 0'a Bölünemez"))
                    if isinstance(result, (int, float)):
                        self.model.appendRow(QStandardItem(f"      {self.format_number(result)}"))
                    else:
                        self.model.appendRow(QStandardItem(result))
                        
                    # Listeyi en alta kaydır
                    self.listView.scrollToBottom()
                    
                else:
                    # Eğer ifade beklenenden farklıysa hata mesajı ekle
                    #♣self.model.appendRow(QStandardItem("Geçersiz ifade formatı"))
                    return
            self.model.appendRow(QStandardItem(f"{operator}_________"))
            self.model.appendRow(QStandardItem(f"      {self.format_number(self.current_result)}"))
            self.model.appendRow(QStandardItem(f"     "))
            self.listView.scrollToBottom()
        except Exception as e:
            #self.model.appendRow(QStandardItem(f"İşlem Hatası: {e}"))
            self.model.appendRow(QStandardItem(f"{operator}_________"))
            self.model.appendRow(QStandardItem(f"      {self.format_number(self.current_result)}"))
            self.model.appendRow(QStandardItem(f"     "))
            self.listView.scrollToBottom()
            return
    def delete_selected_items(self):
        try:
            selected_indexes = self.listView.selectedIndexes()
            if not selected_indexes:
                return
            for index in sorted(selected_indexes, reverse=True):
                self.model.removeRow(index.row())
        except Exception as e:
            print(f"Error deleting items: {e}")

    def clear_listview(self):
        try:
            self.model.clear()
            self.current_result = 0.0
            self.first_operation = True
        except Exception as e:
            print(f"Error clearing list view: {e}")

    def edit_item(self, index):
        try:
            item = self.model.itemFromIndex(index)
            if item is None:
                item = QStandardItem("      ")
                self.model.setItem(index.row(), index.column(), item)
            current_text = item.text()  # Boşlukları koruyarak metni al
            new_text = current_text if current_text.strip() else "Yeni Değer"
            item.setText(new_text)  # Boşlukları koruyarak metni ayarla

            # Düzenleme moduna geç ve imleci sona ayarla
            self.listView.edit(index)
            editor = self.listView.indexWidget(index)
            if editor:
                # İmleci metnin sonuna ayarla
                editor.setCursorPosition(len(editor.text()))

        except Exception as e:
            print(f"Error editing item: {e}")

    def init_database(self):
        try:
            self.conn = sqlite3.connect('G:\\PROGRAM\\HESAPMAKINESI\\hesap.db')
            self.cursor = self.conn.cursor()
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS list_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_text TEXT NOT NULL,
                    date TEXT
                )
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Database initialization error: {e}")

    def save_to_database(self):
        try:
            current_date = datetime.datetime.now().strftime('%Y-%m-%d')
            self.cursor.execute('DELETE FROM list_items WHERE date = ?', (current_date,))
            self.conn.commit()
            for row in range(self.model.rowCount()):
                item_text = self.model.item(row).text()
                if item_text:
                    self.cursor.execute('INSERT INTO list_items (item_text, date) VALUES (?, ?)', (item_text, current_date))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error saving to database: {e}")

    def load_last_record(self):
        try:
            self.cursor.execute('SELECT item_text FROM list_items ORDER BY id DESC')
            rows = self.cursor.fetchall()
            if self.current_index < len(rows):
                self.model.appendRow(QStandardItem(f"{rows[self.current_index][0]}"))
                self.current_index += 1
            self.listView.scrollToBottom()
        except sqlite3.Error as e:
            print(f"Error loading last record: {e}")
    def satir_uzunluguna_gore_bol(self, text, genislik=35):
        # Gelen verinin metin olduğundan emin ol
        if not isinstance(text, str):
            text = str(text)
        
        bolunmus_satirlar = []
        while len(text) > genislik:
            bolunmus_satirlar.append(text[:genislik])
            text = text[genislik:]
        bolunmus_satirlar.append(text)
        return bolunmus_satirlar


    def add_to_listview(self):
        try:
            text = self.textEdit.toPlainText()
            lines = text.splitlines()

            for line in lines:
                # Satır tamamen boşsa boşluk karakteri olarak ekle
                if line.strip() == "":
                    self.model.appendRow(QStandardItem(" "))
                # İşlem satırları (örneğin 90+90 gibi tek satırda girilen işlemler)
                elif any(op in line for op in ['+', '-', '*', '/']) and not line.endswith(tuple('+-*/')):
                    try:
                        result = eval(line.replace(",", "."))
                        operator = [op for op in ['+', '-', '*', '/'] if op in line][0]
                        numbers = line.split(operator)

                        # Sayıları ayrı satırlara ekle
                        for number in numbers:
                            for parca in self.satir_uzunluguna_gore_bol(number, genislik=20):  # strip() kullanmadan ekle
                                self.model.appendRow(QStandardItem(f"      {parca}"))

                        # Operatör ve sonucu ekle
                        self.model.appendRow(QStandardItem(f"{operator}_________"))
                        for parca in self.satir_uzunluguna_gore_bol(self.format_number(result), genislik=20):
                            self.model.appendRow(QStandardItem(f"      {parca}"))

                        # Her işlemden sonra boş satır ekleyerek alt satıra geç
                        self.model.appendRow(QStandardItem(""))

                    except Exception:
                        for parca in self.satir_uzunluguna_gore_bol(line, genislik=35):
                            self.model.appendRow(QStandardItem(f"      {parca}"))

                # Sayı satırları
                elif line.replace(',', '').replace('.', '').isdigit():
                    for parca in self.satir_uzunluguna_gore_bol(line, genislik=20):
                        self.model.appendRow(QStandardItem(f"      {parca}"))

                # Tekli operatörler
                elif line in ['+', '-', '*', '/']:
                    self.calculate_result(line)
                    self.model.appendRow(QStandardItem(" "))  # Operatörden sonra alt satıra geç

                # Diğer durumlar (boşlukları koruyarak ekler)
                else:
                    for parca in self.satir_uzunluguna_gore_bol(line, genislik=35):
                        self.model.appendRow(QStandardItem(parca))  # Boşlukları koruyarak ekle

            # Listeyi güncelle ve kaydet
            self.listView.scrollToBottom()
            self.save_to_database()
            self.textEdit.clear()

        except Exception as e:
            print(f"Error adding to list view: {e}")


    def load_all_today_records(self):
        try:
            self.cursor.execute('SELECT item_text FROM list_items')
            rows = self.cursor.fetchall()
            self.model.clear()
            for row in rows:
                self.model.appendRow(QStandardItem(f"      {row[0]}"))
            self.listView.scrollToBottom()
            self.listView.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        except sqlite3.Error as e:
            print(f"Error loading records: {e}")

    def get_records_by_date(self):
        try:
            date_str, ok = QInputDialog.getText(self, 'Tarih Gir...', '')
            if ok and date_str:
                selected_date = datetime.datetime.strptime(date_str, '%d.%m.%Y').date()
                self.cursor.execute('SELECT item_text FROM list_items WHERE date = ?', (selected_date,))
                rows = self.cursor.fetchall()
                self.model.clear()
                for row in rows:
                    self.model.appendRow(QStandardItem(f"      {row[0]}"))
                self.listView.scrollToBottom()
        except (ValueError, sqlite3.Error) as e:
            print(f"Error getting records by date: {e}")
    def list_view_clicked(self, index):
        try:
            # Listeden seçilen değeri al
            item = self.model.itemFromIndex(index)
            if item:
                self.selected_value = float(item.text().strip())
        except ValueError:
            print("Geçersiz seçim, sayı değil.")

    def add_operator(self, operator):
        try:
            # Bekleyen operatörü sakla
            self.pending_operator = operator
            # Operatörü listeye ekle
            self.model.appendRow(QStandardItem(f"{operator}"))
        except Exception as e:
            print(f"Error adding operator: {e}")
    def list_view_clicked(self, index):
        try:
            # Listeden seçilen değeri al
            item = self.model.itemFromIndex(index)
            if item:
                self.selected_value = float(item.text().strip())
        except ValueError:
            print("Geçersiz seçim, sayı değil.")
    def calculate_from_selection(self):
        try:
            if self.selected_value is None or self.pending_operator is None:
                return

            # Sonuç hesapla
            current_result = self.current_result  # Önceki sonuç (önceki işlemlerden)
            if self.pending_operator == "+":
                current_result += self.selected_value
            elif self.pending_operator == "-":
                current_result -= self.selected_value
            elif self.pending_operator == "*":
                current_result *= self.selected_value
            elif self.pending_operator == "/":
                if self.selected_value != 0:
                    current_result /= self.selected_value
                else:
                    self.model.appendRow(QStandardItem("Bölme Hatası: 0'a Bölünemez"))
                    return

            # Sonucu listeye ekle
            self.model.appendRow(QStandardItem(f"= {self.format_number(current_result)}"))
            # Sonucu sakla
            self.current_result = current_result
            # Durumları sıfırla
            self.selected_value = None
            self.pending_operator = None
        except Exception as e:
            print(f"Error calculating result: {e}")

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
