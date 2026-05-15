import sys
import sqlite3
from datetime import datetime
from contextlib import contextmanager
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QDialog, QLabel,
    QLineEdit, QComboBox, QMessageBox, QTabWidget, QFrame, QSpinBox,
    QDoubleSpinBox, QHeaderView, QGridLayout, QTextEdit, QGroupBox,
    QScrollArea, QSplitter
)
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QFont, QColor, QIcon, QPalette
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


# ===================== VERİTABANI YÖNETİCİSİ =====================

class DatabaseManager:
    def __init__(self, db_name="fitness_takip.db"):
        self.db_name = db_name
        self.create_tables()
        self.ornek_veri_ekle()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def create_tables(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sporcular (
                    sporcu_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ad TEXT NOT NULL,
                    soyad TEXT NOT NULL,
                    yas INTEGER,
                    kilo REAL NOT NULL,
                    boy REAL NOT NULL,
                    cinsiyet TEXT,
                    hedef TEXT,
                    kayit_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS antrenmanlar (
                    antrenman_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ad TEXT NOT NULL,
                    kategori TEXT NOT NULL,
                    saat INTEGER NOT NULL,
                    dakika INTEGER NOT NULL,
                    zorluk_seviyesi TEXT DEFAULT 'Orta',
                    aciklama TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS takipler (
                    takip_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sporcu_id INTEGER NOT NULL,
                    antrenman_id INTEGER NOT NULL,
                    kalori INTEGER NOT NULL,
                    nabiz INTEGER,
                    notlar TEXT,
                    tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sporcu_id) REFERENCES sporcular(sporcu_id),
                    FOREIGN KEY (antrenman_id) REFERENCES antrenmanlar(antrenman_id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ilerlemeler (
                    ilerleme_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sporcu_id INTEGER NOT NULL,
                    kilo REAL NOT NULL,
                    tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sporcu_id) REFERENCES sporcular(sporcu_id)
                )
            ''')

    def ornek_veri_ekle(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM sporcular')
            if cursor.fetchone()[0] == 0:
                ornek_sporcular = [
                    ("Ahmet", "Yılmaz", 28, 75.5, 178, "Erkek", "Kilo Verme"),
                    ("Ayşe", "Demir", 25, 62.0, 165, "Kadın", "Kas Kazanma"),
                    ("Mehmet", "Kaya", 32, 85.0, 182, "Erkek", "Form Koruma"),
                    ("Zeynep", "Çelik", 23, 55.5, 162, "Kadın", "Kilo Verme"),
                    ("Can", "Yıldız", 29, 70.0, 175, "Erkek", "Dayanıklılık"),
                ]
                for sporcu in ornek_sporcular:
                    cursor.execute('''
                        INSERT INTO sporcular (ad, soyad, yas, kilo, boy, cinsiyet, hedef)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', sporcu)

            cursor.execute('SELECT COUNT(*) FROM antrenmanlar')
            if cursor.fetchone()[0] == 0:
                ornek_antrenmanlar = [
                    ("Koşu", "Kardiyo", 0, 30, "Kolay", "Tempolu koşu - 5km"),
                    ("Yüzme", "Kardiyo", 1, 0, "Orta", "Serbest yüzme - 1500m"),
                    ("Ağırlık", "Kuvvet", 1, 0, "Zor", "Full body workout"),
                    ("Yoga", "Esneklik", 1, 0, "Kolay", "Gevşeme ve esneme hareketleri"),
                    ("Bisiklet", "Kardiyo", 0, 45, "Orta", "Düşük tempolu bisiklet"),
                    ("HIIT", "Kardiyo", 0, 20, "Zor", "Yüksek tempolu interval antrenmanı"),
                    ("Pilates", "Esneklik", 0, 45, "Orta", "Core çalışması ve duruş"),
                ]
                for antrenman in ornek_antrenmanlar:
                    cursor.execute('''
                        INSERT INTO antrenmanlar (ad, kategori, saat, dakika, zorluk_seviyesi, aciklama)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', antrenman)

    def sporcu_ekle(self, ad, soyad, yas, kilo, boy, cinsiyet, hedef):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sporcular (ad, soyad, yas, kilo, boy, cinsiyet, hedef)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (ad, soyad, yas, kilo, boy, cinsiyet, hedef))
            return cursor.lastrowid

    def sporcu_sil(self, sporcu_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM takipler WHERE sporcu_id = ?', (sporcu_id,))
            cursor.execute('DELETE FROM ilerlemeler WHERE sporcu_id = ?', (sporcu_id,))
            cursor.execute('DELETE FROM sporcular WHERE sporcu_id = ?', (sporcu_id,))
            return True

    def sporculari_getir(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM sporcular ORDER BY kayit_tarihi DESC')
            return [dict(row) for row in cursor.fetchall()]

    def antrenman_ekle(self, ad, kategori, saat, dakika, zorluk, aciklama):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO antrenmanlar (ad, kategori, saat, dakika, zorluk_seviyesi, aciklama)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (ad, kategori, saat, dakika, zorluk, aciklama))
            return cursor.lastrowid

    def antrenman_sil(self, antrenman_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM takipler WHERE antrenman_id = ?', (antrenman_id,))
            cursor.execute('DELETE FROM antrenmanlar WHERE antrenman_id = ?', (antrenman_id,))
            return True

    def antrenmanlari_getir(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM antrenmanlar ORDER BY antrenman_id')
            return [dict(row) for row in cursor.fetchall()]

    def takip_ekle(self, sporcu_id, antrenman_id, kalori, nabiz, notlar):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO takipler (sporcu_id, antrenman_id, kalori, nabiz, notlar)
                VALUES (?, ?, ?, ?, ?)
            ''', (sporcu_id, antrenman_id, kalori, nabiz, notlar))
            return cursor.lastrowid

    def takipler_getir(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT t.*, s.ad as sporcu_ad, s.soyad as sporcu_soyad,
                       a.ad as antrenman_ad, a.kategori as antrenman_kategori
                FROM takipler t
                JOIN sporcular s ON t.sporcu_id = s.sporcu_id
                JOIN antrenmanlar a ON t.antrenman_id = a.antrenman_id
                ORDER BY t.tarih DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]

    def ilerleme_kaydet(self, sporcu_id, kilo):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE sporcular SET kilo = ? WHERE sporcu_id = ?', (kilo, sporcu_id))
            cursor.execute('''
                INSERT INTO ilerlemeler (sporcu_id, kilo)
                VALUES (?, ?)
            ''', (sporcu_id, kilo))

    def ilerlemeleri_getir(self, sporcu_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM ilerlemeler WHERE sporcu_id = ? ORDER BY tarih', (sporcu_id,))
            return [dict(row) for row in cursor.fetchall()]

    def istatistikler(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as toplam_sporcu FROM sporcular')
            toplam_sporcu = cursor.fetchone()['toplam_sporcu']

            cursor.execute('SELECT COUNT(*) as toplam_antrenman FROM antrenmanlar')
            toplam_antrenman = cursor.fetchone()['toplam_antrenman']

            cursor.execute('SELECT COUNT(*) as toplam_takip FROM takipler')
            toplam_takip = cursor.fetchone()['toplam_takip']

            cursor.execute('SELECT SUM(kalori) as toplam_kalori FROM takipler')
            toplam_kalori = cursor.fetchone()['toplam_kalori'] or 0

            cursor.execute('''
                SELECT kategori, COUNT(*) as sayi
                FROM antrenmanlar GROUP BY kategori
            ''')
            kategori_dagilimi = [dict(row) for row in cursor.fetchall()]

            return {
                "toplam_sporcu": toplam_sporcu,
                "toplam_antrenman": toplam_antrenman,
                "toplam_takip": toplam_takip,
                "toplam_kalori": toplam_kalori,
                "kategori_dagilimi": kategori_dagilimi
            }


# ===================== DİALOG PENCERELERİ =====================

class SporcuEkleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("➕ Yeni Sporcu Ekle")
        self.setGeometry(100, 100, 500, 580)
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a2e;
                border-radius: 15px;
            }
            QLabel {
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
            }
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: #2d2d3a;
                color: #ffffff;
                border: 2px solid #f5a623;
                border-radius: 10px;
                padding: 10px;
                font-size: 12px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #4CAF50;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 10px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.result = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        baslik = QLabel("🏃 YENİ SPORCU KAYDI")
        baslik.setFont(QFont("Arial", 16, QFont.Bold))
        baslik.setStyleSheet("color: #f5a623;")
        baslik.setAlignment(Qt.AlignCenter)
        layout.addWidget(baslik)

        grid = QGridLayout()
        grid.setSpacing(15)

        grid.addWidget(QLabel("Ad:"), 0, 0)
        self.ad_input = QLineEdit()
        self.ad_input.setPlaceholderText("Sporcu adı")
        grid.addWidget(self.ad_input, 0, 1)

        grid.addWidget(QLabel("Soyad:"), 1, 0)
        self.soyad_input = QLineEdit()
        self.soyad_input.setPlaceholderText("Sporcu soyadı")
        grid.addWidget(self.soyad_input, 1, 1)

        grid.addWidget(QLabel("Yaş:"), 2, 0)
        self.yas_input = QSpinBox()
        self.yas_input.setRange(12, 100)
        self.yas_input.setValue(25)
        grid.addWidget(self.yas_input, 2, 1)

        grid.addWidget(QLabel("Kilo (kg):"), 3, 0)
        self.kilo_input = QDoubleSpinBox()
        self.kilo_input.setRange(20, 300)
        self.kilo_input.setDecimals(1)
        self.kilo_input.setValue(70)
        grid.addWidget(self.kilo_input, 3, 1)

        grid.addWidget(QLabel("Boy (cm):"), 4, 0)
        self.boy_input = QDoubleSpinBox()
        self.boy_input.setRange(100, 250)
        self.boy_input.setValue(170)
        grid.addWidget(self.boy_input, 4, 1)

        grid.addWidget(QLabel("Cinsiyet:"), 5, 0)
        self.cinsiyet_combo = QComboBox()
        self.cinsiyet_combo.addItems(["Erkek", "Kadın"])
        grid.addWidget(self.cinsiyet_combo, 5, 1)

        grid.addWidget(QLabel("Hedef:"), 6, 0)
        self.hedef_combo = QComboBox()
        self.hedef_combo.addItems(["Kilo Verme", "Kas Kazanma", "Form Koruma", "Dayanıklılık"])
        grid.addWidget(self.hedef_combo, 6, 1)

        layout.addLayout(grid)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        ekle_btn = QPushButton("✅ SPORCU EKLE")
        ekle_btn.clicked.connect(self.ekle)
        iptal_btn = QPushButton("❌ İPTAL")
        iptal_btn.setStyleSheet("background-color: #e63946;")
        iptal_btn.clicked.connect(self.reject)

        button_layout.addWidget(ekle_btn)
        button_layout.addWidget(iptal_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def ekle(self):
        ad = self.ad_input.text().strip()
        soyad = self.soyad_input.text().strip()
        if not ad or not soyad:
            QMessageBox.warning(self, "Hata", "Ad ve Soyad zorunludur!")
            return
        self.result = (ad, soyad, self.yas_input.value(), self.kilo_input.value(),
                      self.boy_input.value(), self.cinsiyet_combo.currentText(),
                      self.hedef_combo.currentText())
        self.accept()


class AntrenmanEkleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("💪 Yeni Antrenman Ekle")
        self.setGeometry(100, 100, 500, 520)
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a2e;
                border-radius: 15px;
            }
            QLabel {
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
            }
            QLineEdit, QComboBox, QSpinBox, QTextEdit {
                background-color: #2d2d3a;
                color: #ffffff;
                border: 2px solid #f5a623;
                border-radius: 10px;
                padding: 10px;
                font-size: 12px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #4CAF50;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 10px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.result = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        baslik = QLabel("💪 YENİ ANTRENMAN")
        baslik.setFont(QFont("Arial", 16, QFont.Bold))
        baslik.setStyleSheet("color: #f5a623;")
        baslik.setAlignment(Qt.AlignCenter)
        layout.addWidget(baslik)

        grid = QGridLayout()
        grid.setSpacing(15)

        grid.addWidget(QLabel("Antrenman Adı:"), 0, 0)
        self.ad_input = QLineEdit()
        self.ad_input.setPlaceholderText("Örn: Koşu, Yüzme, Ağırlık")
        grid.addWidget(self.ad_input, 0, 1)

        grid.addWidget(QLabel("Kategori:"), 1, 0)
        self.kategori_combo = QComboBox()
        self.kategori_combo.addItems(["Kardiyo", "Kuvvet", "Esneklik", "Denge", "HIIT"])
        grid.addWidget(self.kategori_combo, 1, 1)

        grid.addWidget(QLabel("Süre:"), 2, 0)
        sure_layout = QHBoxLayout()
        self.saat_input = QSpinBox()
        self.saat_input.setRange(0, 5)
        self.saat_input.setPrefix("Saat: ")
        self.dakika_input = QSpinBox()
        self.dakika_input.setRange(0, 59)
        self.dakika_input.setPrefix("Dakika: ")
        sure_layout.addWidget(self.saat_input)
        sure_layout.addWidget(self.dakika_input)
        grid.addLayout(sure_layout, 2, 1)

        grid.addWidget(QLabel("Zorluk Seviyesi:"), 3, 0)
        self.zorluk_combo = QComboBox()
        self.zorluk_combo.addItems(["Kolay", "Orta", "Zor", "Profesyonel"])
        grid.addWidget(self.zorluk_combo, 3, 1)

        grid.addWidget(QLabel("Açıklama:"), 4, 0)
        self.aciklama_input = QTextEdit()
        self.aciklama_input.setMaximumHeight(100)
        self.aciklama_input.setPlaceholderText("Antrenman açıklaması...")
        grid.addWidget(self.aciklama_input, 4, 1)

        layout.addLayout(grid)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        ekle_btn = QPushButton("✅ ANTRENMAN EKLE")
        ekle_btn.clicked.connect(self.ekle)
        iptal_btn = QPushButton("❌ İPTAL")
        iptal_btn.setStyleSheet("background-color: #e63946;")
        iptal_btn.clicked.connect(self.reject)

        button_layout.addWidget(ekle_btn)
        button_layout.addWidget(iptal_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def ekle(self):
        ad = self.ad_input.text().strip()
        if not ad:
            QMessageBox.warning(self, "Hata", "Antrenman adı giriniz!")
            return
        if self.saat_input.value() == 0 and self.dakika_input.value() == 0:
            QMessageBox.warning(self, "Hata", "Süre giriniz!")
            return
        self.result = (ad, self.kategori_combo.currentText(), self.saat_input.value(),
                      self.dakika_input.value(), self.zorluk_combo.currentText(),
                      self.aciklama_input.toPlainText().strip())
        self.accept()


class TakipEkleDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("📊 Takip Oluştur")
        self.setGeometry(100, 100, 500, 480)
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a2e;
                border-radius: 15px;
            }
            QLabel {
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
            }
            QComboBox, QSpinBox, QTextEdit {
                background-color: #2d2d3a;
                color: #ffffff;
                border: 2px solid #f5a623;
                border-radius: 10px;
                padding: 10px;
                font-size: 12px;
            }
            QComboBox:focus {
                border: 2px solid #4CAF50;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 10px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.result = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        baslik = QLabel("📊 YENİ TAKİP KAYDI")
        baslik.setFont(QFont("Arial", 16, QFont.Bold))
        baslik.setStyleSheet("color: #f5a623;")
        baslik.setAlignment(Qt.AlignCenter)
        layout.addWidget(baslik)

        grid = QGridLayout()
        grid.setSpacing(15)

        grid.addWidget(QLabel("Sporcu:"), 0, 0)
        self.sporcu_combo = QComboBox()
        for s in self.db.sporculari_getir():
            self.sporcu_combo.addItem(f"🏃 {s['ad']} {s['soyad']} - {s['kilo']} kg", s['sporcu_id'])
        grid.addWidget(self.sporcu_combo, 0, 1)

        grid.addWidget(QLabel("Antrenman:"), 1, 0)
        self.antrenman_combo = QComboBox()
        for a in self.db.antrenmanlari_getir():
            sure = f"{a['saat']}s {a['dakika']}dk" if a['saat'] > 0 else f"{a['dakika']}dk"
            self.antrenman_combo.addItem(f"💪 {a['ad']} ({sure}) - {a['zorluk_seviyesi']}", a['antrenman_id'])
        grid.addWidget(self.antrenman_combo, 1, 1)

        grid.addWidget(QLabel("Yakılan Kalori:"), 2, 0)
        self.kalori_input = QSpinBox()
        self.kalori_input.setRange(0, 2000)
        self.kalori_input.setValue(300)
        grid.addWidget(self.kalori_input, 2, 1)

        grid.addWidget(QLabel("Ortalama Nabız:"), 3, 0)
        self.nabiz_input = QSpinBox()
        self.nabiz_input.setRange(0, 220)
        self.nabiz_input.setValue(120)
        grid.addWidget(self.nabiz_input, 3, 1)

        grid.addWidget(QLabel("Notlar:"), 4, 0)
        self.notlar_input = QTextEdit()
        self.notlar_input.setMaximumHeight(80)
        self.notlar_input.setPlaceholderText("Eklemek istediğiniz notlar...")
        grid.addWidget(self.notlar_input, 4, 1)

        layout.addLayout(grid)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        ekle_btn = QPushButton("✅ TAKİP OLUŞTUR")
        ekle_btn.clicked.connect(self.ekle)
        iptal_btn = QPushButton("❌ İPTAL")
        iptal_btn.setStyleSheet("background-color: #e63946;")
        iptal_btn.clicked.connect(self.reject)

        button_layout.addWidget(ekle_btn)
        button_layout.addWidget(iptal_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def ekle(self):
        if self.sporcu_combo.currentData() is None or self.antrenman_combo.currentData() is None:
            QMessageBox.warning(self, "Hata", "Lütfen sporcu ve antrenman seçin!")
            return
        self.result = (self.sporcu_combo.currentData(), self.antrenman_combo.currentData(),
                      self.kalori_input.value(), self.nabiz_input.value(),
                      self.notlar_input.toPlainText().strip())
        self.accept()


class IlerlemeKaydetDialog(QDialog):
    def __init__(self, sporcu_adi, mevcut_kilo, parent=None):
        super().__init__(parent)
        self.result = None
        self.setWindowTitle("📈 İlerleme Kaydet")
        self.setGeometry(100, 100, 400, 320)
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a2e;
                border-radius: 15px;
            }
            QLabel {
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
            }
            QDoubleSpinBox {
                background-color: #2d2d3a;
                color: #ffffff;
                border: 2px solid #f5a623;
                border-radius: 10px;
                padding: 10px;
                font-size: 12px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 10px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.sporcu_adi = sporcu_adi
        self.mevcut_kilo = mevcut_kilo
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        baslik = QLabel("📈 İLERLEME KAYDET")
        baslik.setFont(QFont("Arial", 16, QFont.Bold))
        baslik.setStyleSheet("color: #f5a623;")
        baslik.setAlignment(Qt.AlignCenter)
        layout.addWidget(baslik)

        grid = QGridLayout()
        grid.setSpacing(15)

        grid.addWidget(QLabel("Sporcu:"), 0, 0)
        sporcu_label = QLabel(f"🏃 {self.sporcu_adi}")
        sporcu_label.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 14px;")
        grid.addWidget(sporcu_label, 0, 1)

        grid.addWidget(QLabel("Mevcut Kilo:"), 1, 0)
        mevcut_label = QLabel(f"{self.mevcut_kilo} kg")
        mevcut_label.setStyleSheet("color: #ffffff; font-size: 14px;")
        grid.addWidget(mevcut_label, 1, 1)

        grid.addWidget(QLabel("Yeni Kilo (kg):"), 2, 0)
        self.kilo_input = QDoubleSpinBox()
        self.kilo_input.setRange(20, 300)
        self.kilo_input.setDecimals(1)
        self.kilo_input.setValue(self.mevcut_kilo)
        grid.addWidget(self.kilo_input, 2, 1)

        layout.addLayout(grid)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        kaydet_btn = QPushButton("✅ KAYDET")
        kaydet_btn.clicked.connect(self.kaydet)
        iptal_btn = QPushButton("❌ İPTAL")
        iptal_btn.setStyleSheet("background-color: #e63946;")
        iptal_btn.clicked.connect(self.reject)

        button_layout.addWidget(kaydet_btn)
        button_layout.addWidget(iptal_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def kaydet(self):
        self.result = self.kilo_input.value()
        self.accept()


# ===================== GRAFİKLER =====================

class StatisticsWidget(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.figure = Figure(figsize=(12, 5), dpi=100, facecolor='#1a1a2e')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: #1a1a2e; border-radius: 15px;")
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def update_charts(self):
        self.figure.clear()
        istatistikler = self.db.istatistikler()

        ax1 = self.figure.add_subplot(121)
        ax1.set_facecolor('#2d2d3a')
        if istatistikler['kategori_dagilimi']:
            kategoriler = [k['kategori'] for k in istatistikler['kategori_dagilimi']]
            sayilar = [k['sayi'] for k in istatistikler['kategori_dagilimi']]
            colors = ['#f5a623', '#4CAF50', '#e63946', '#2196F3', '#9c27b0']
            wedges, texts, autotexts = ax1.pie(sayilar, labels=kategoriler, autopct='%1.1f%%',
                                                colors=colors[:len(kategoriler)], startangle=90)
            for text in texts:
                text.set_color('#ffffff')
                text.set_fontsize(9)
            for autotext in autotexts:
                autotext.set_color('#ffffff')
                autotext.set_fontweight('bold')
            ax1.set_title('Antrenman Kategori Dağılımı', fontsize=12, fontweight='bold', color='#f5a623')

        ax2 = self.figure.add_subplot(122)
        ax2.set_facecolor('#2d2d3a')
        labels = ['🏃 Sporcular', '💪 Antrenmanlar', '📊 Takipler']
        values = [istatistikler['toplam_sporcu'], istatistikler['toplam_antrenman'], istatistikler['toplam_takip']]
        colors = ['#f5a623', '#4CAF50', '#2196F3']
        bars = ax2.bar(labels, values, color=colors, edgecolor='none', width=0.6)
        ax2.set_title('Sistem İstatistikleri', fontsize=12, fontweight='bold', color='#f5a623')
        ax2.set_ylabel('Sayı', fontsize=10, fontweight='bold', color='#ffffff')
        ax2.tick_params(axis='y', colors='#ffffff')
        ax2.tick_params(axis='x', colors='#ffffff', labelsize=10)

        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5, f'{int(height)}',
                    ha='center', va='bottom', fontweight='bold', fontsize=11, color='#f5a623')

        self.figure.tight_layout()
        self.canvas.draw()


class IlerlemeGrafikWidget(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.figure = Figure(figsize=(10, 4), dpi=100, facecolor='#1a1a2e')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: #1a1a2e; border-radius: 15px;")
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def update_chart(self, sporcu_id):
        self.figure.clear()
        ilerlemeler = self.db.ilerlemeleri_getir(sporcu_id)

        ax = self.figure.add_subplot(111)
        ax.set_facecolor('#2d2d3a')

        if len(ilerlemeler) >= 2:
            tarihler = [i['tarih'][5:10] for i in ilerlemeler]
            kilolar = [i['kilo'] for i in ilerlemeler]

            ax.plot(range(len(tarihler)), kilolar, marker='o', linewidth=2, markersize=8, color='#f5a623')
            ax.fill_between(range(len(tarihler)), kilolar, color='#f5a623', alpha=0.2)

            ax.set_xticks(range(len(tarihler)))
            ax.set_xticklabels(tarihler, rotation=45, ha='right')

            ax.set_title('Kilo Değişim Grafiği', fontsize=12, fontweight='bold', color='#f5a623')
            ax.set_xlabel('Tarih', fontsize=10, fontweight='bold', color='#ffffff')
            ax.set_ylabel('Kilo (kg)', fontsize=10, fontweight='bold', color='#ffffff')
            ax.tick_params(axis='x', colors='#ffffff')
            ax.tick_params(axis='y', colors='#ffffff')
            ax.grid(True, alpha=0.3, color='#4CAF50')

            baslangic = ilerlemeler[0]['kilo']
            son = ilerlemeler[-1]['kilo']
            fark = son - baslangic
            fark_str = f"{fark:+.1f} kg"
            renk = '#4CAF50' if fark < 0 else '#e63946'
            ax.text(0.02, 0.95, f"Değişim: {fark_str}", transform=ax.transAxes,
                   fontsize=11, color=renk, fontweight='bold',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='#1a1a2e', alpha=0.8))
        else:
            ax.text(0.5, 0.5, '📊 Yeterli veri yok\nEn az 2 ölçüm gerekiyor',
                   ha='center', va='center', fontsize=12, color='#f5a623')
            ax.set_title('Kilo Değişim Grafiği', fontsize=12, fontweight='bold', color='#f5a623')

        self.figure.tight_layout()
        self.canvas.draw()


# ===================== ANA PENCERE =====================

class FitnessTakipUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.setWindowTitle("💪 PROFESYONEL FITNESS TAKİP SİSTEMİ")
        self.setGeometry(50, 50, 1450, 900)

        # ANA TEMA RENKLERİ: SARI (#f5a623), YEŞİL (#4CAF50), SİYAH (#1a1a2e)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a2e;
            }
            QWidget {
                background-color: transparent;
            }
            QLabel {
                color: #ffffff;
            }
            QTabWidget::pane {
                background-color: #2d2d3a;
                border-radius: 15px;
                border: none;
            }
            QTabBar::tab {
                background-color: #1a1a2e;
                color: #ffffff;
                padding: 12px 40px;
                border-radius: 10px;
                font-weight: bold;
                font-size: 13px;
                margin-right: 8px;
            }
            QTabBar::tab:selected {
                background-color: #f5a623;
                color: #1a1a2e;
            }
            QTabBar::tab:hover:!selected {
                background-color: #4CAF50;
                color: #ffffff;
            }
            QTableWidget {
                background-color: #2d2d3a;
                alternate-background-color: #3d3d4a;
                color: #ffffff;
                gridline-color: #4CAF50;
                border: none;
                border-radius: 12px;
            }
            QTableWidget::item {
                padding: 12px;
            }
            QTableWidget::item:selected {
                background-color: #f5a623;
                color: #1a1a2e;
            }
            QHeaderView::section {
                background-color: #1a1a2e;
                color: #f5a623;
                font-weight: bold;
                padding: 12px;
                border: none;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 25px;
                border-radius: 10px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox, QTextEdit {
                background-color: #2d2d3a;
                border: 2px solid #f5a623;
                border-radius: 10px;
                padding: 10px;
                color: #ffffff;
                font-size: 12px;
            }
            QComboBox:focus, QLineEdit:focus {
                border: 2px solid #4CAF50;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d3a;
                color: #ffffff;
                selection-background-color: #f5a623;
            }
            QScrollBar:vertical {
                background-color: #2d2d3a;
                border-radius: 8px;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background-color: #f5a623;
                border-radius: 8px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #4CAF50;
            }
        """)

        self.init_ui()
        self.load_data()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # HEADER - PROFESYONEL MENU
        header_widget = QFrame()
        header_widget.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1a1a2e, stop:0.5 #2d2d3a, stop:1 #1a1a2e);
                border-radius: 15px;
                border: 2px solid #f5a623;
            }
        """)
        header_widget.setFixedHeight(80)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(30, 0, 30, 0)

        logo_label = QLabel("💪")
        logo_label.setFont(QFont("Arial", 32, QFont.Bold))
        logo_label.setStyleSheet("color: #f5a623;")
        header_layout.addWidget(logo_label)

        title_label = QLabel("PROFESYONEL FITNESS TAKİP SİSTEMİ")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setStyleSheet("color: #f5a623;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        tarih_label = QLabel(datetime.now().strftime("%d.%m.%Y %H:%M"))
        tarih_label.setFont(QFont("Arial", 11))
        tarih_label.setStyleSheet("color: #4CAF50; padding: 8px 15px; background-color: #1a1a2e; border-radius: 10px;")
        header_layout.addWidget(tarih_label)

        header_widget.setLayout(header_layout)

        # DASHBOARD KARTLARI
        dashboard_layout = QHBoxLayout()
        dashboard_layout.setSpacing(20)

        self.sporcu_card = self.create_dashboard_card("🏃 SPORCULAR", "0", "#f5a623")
        self.antrenman_card = self.create_dashboard_card("💪 ANTRENMANLAR", "0", "#4CAF50")
        self.takip_card = self.create_dashboard_card("📊 TAKİPLER", "0", "#2196F3")
        self.kalori_card = self.create_dashboard_card("🔥 TOPLAM KALORİ", "0 kcal", "#e63946")

        dashboard_layout.addWidget(self.sporcu_card)
        dashboard_layout.addWidget(self.antrenman_card)
        dashboard_layout.addWidget(self.takip_card)
        dashboard_layout.addWidget(self.kalori_card)

        # SEKMELER
        self.tabs = QTabWidget()

        self.sporcu_tab = self.create_sporcu_tab()
        self.tabs.addTab(self.sporcu_tab, "🏃 SPORCULAR")

        self.antrenman_tab = self.create_antrenman_tab()
        self.tabs.addTab(self.antrenman_tab, "💪 ANTRENMANLAR")

        self.takip_tab = self.create_takip_tab()
        self.tabs.addTab(self.takip_tab, "📊 TAKİPLER")

        self.stats_widget = StatisticsWidget(self.db)
        self.tabs.addTab(self.stats_widget, "📈 İSTATİSTİKLER")

        main_layout.addWidget(header_widget)
        main_layout.addLayout(dashboard_layout)
        main_layout.addWidget(self.tabs)

        central_widget.setLayout(main_layout)

        # TIMER
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_all)
        self.timer.start(5000)

    def create_dashboard_card(self, title, value, color):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #2d2d3a;
                border-radius: 15px;
                border-left: 8px solid {color};
                min-width: 200px;
            }}
        """)
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 11, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"color: {color};")

        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 28, QFont.Bold))
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet("color: white;")
        value_label.setObjectName("value_label")

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        card.setLayout(layout)
        return card

    def create_sporcu_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        ekle_btn = QPushButton("➕ YENİ SPORCU")
        ekle_btn.setStyleSheet("background-color: #4CAF50;")
        ekle_btn.clicked.connect(self.sporcu_ekle)

        sil_btn = QPushButton("🗑️ SİL")
        sil_btn.setStyleSheet("background-color: #e63946;")
        sil_btn.clicked.connect(self.sporcu_sil)

        ilerleme_btn = QPushButton("📈 İLERLEME KAYDET")
        ilerleme_btn.setStyleSheet("background-color: #f5a623; color: #1a1a2e;")
        ilerleme_btn.clicked.connect(self.ilerleme_kaydet)

        grafik_btn = QPushButton("📊 İLERLEME GRAFİĞİ")
        grafik_btn.setStyleSheet("background-color: #2196F3;")
        grafik_btn.clicked.connect(self.ilerleme_grafigi)

        yenile_btn = QPushButton("🔄 YENİLE")
        yenile_btn.clicked.connect(self.sporculari_listele)

        button_layout.addWidget(ekle_btn)
        button_layout.addWidget(sil_btn)
        button_layout.addWidget(ilerleme_btn)
        button_layout.addWidget(grafik_btn)
        button_layout.addWidget(yenile_btn)
        button_layout.addStretch()

        self.sporcu_table = QTableWidget()
        self.sporcu_table.setColumnCount(8)
        self.sporcu_table.setHorizontalHeaderLabels(["ID", "AD", "SOYAD", "YAŞ", "KİLO", "BOY", "CİNSİYET", "HEDEF"])
        self.sporcu_table.setAlternatingRowColors(True)
        self.sporcu_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addLayout(button_layout)
        layout.addWidget(self.sporcu_table)
        widget.setLayout(layout)
        return widget

    def create_antrenman_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        ekle_btn = QPushButton("➕ YENİ ANTRENMAN")
        ekle_btn.setStyleSheet("background-color: #4CAF50;")
        ekle_btn.clicked.connect(self.antrenman_ekle)

        sil_btn = QPushButton("🗑️ SİL")
        sil_btn.setStyleSheet("background-color: #e63946;")
        sil_btn.clicked.connect(self.antrenman_sil)

        yenile_btn = QPushButton("🔄 YENİLE")
        yenile_btn.clicked.connect(self.antrenmanlari_listele)

        button_layout.addWidget(ekle_btn)
        button_layout.addWidget(sil_btn)
        button_layout.addWidget(yenile_btn)
        button_layout.addStretch()

        self.antrenman_table = QTableWidget()
        self.antrenman_table.setColumnCount(6)
        self.antrenman_table.setHorizontalHeaderLabels(["ID", "AD", "KATEGORİ", "SÜRE", "ZORLUK", "AÇIKLAMA"])
        self.antrenman_table.setAlternatingRowColors(True)
        self.antrenman_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addLayout(button_layout)
        layout.addWidget(self.antrenman_table)
        widget.setLayout(layout)
        return widget

    def create_takip_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        ekle_btn = QPushButton("➕ TAKİP OLUŞTUR")
        ekle_btn.setStyleSheet("background-color: #4CAF50;")
        ekle_btn.clicked.connect(self.takip_ekle)

        yenile_btn = QPushButton("🔄 YENİLE")
        yenile_btn.clicked.connect(self.takipleri_listele)

        button_layout.addWidget(ekle_btn)
        button_layout.addWidget(yenile_btn)
        button_layout.addStretch()

        self.takip_table = QTableWidget()
        self.takip_table.setColumnCount(7)
        self.takip_table.setHorizontalHeaderLabels(["ID", "SPORCU", "ANTRENMAN", "KALORİ", "NABIZ", "TARİH", "NOTLAR"])
        self.takip_table.setAlternatingRowColors(True)
        self.takip_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addLayout(button_layout)
        layout.addWidget(self.takip_table)
        widget.setLayout(layout)
        return widget

    def load_data(self):
        self.sporculari_listele()
        self.antrenmanlari_listele()
        self.takipleri_listele()
        self.update_dashboard()

    def refresh_all(self):
        self.sporculari_listele()
        self.antrenmanlari_listele()
        self.takipleri_listele()
        self.update_dashboard()
        self.stats_widget.update_charts()

    def update_dashboard(self):
        istatistikler = self.db.istatistikler()
        self.sporcu_card.findChild(QLabel, "value_label").setText(str(istatistikler["toplam_sporcu"]))
        self.antrenman_card.findChild(QLabel, "value_label").setText(str(istatistikler["toplam_antrenman"]))
        self.takip_card.findChild(QLabel, "value_label").setText(str(istatistikler["toplam_takip"]))
        self.kalori_card.findChild(QLabel, "value_label").setText(f"{istatistikler['toplam_kalori']} kcal")

    def sporculari_listele(self):
        sporcular = self.db.sporculari_getir()
        self.sporcu_table.setRowCount(0)
        for s in sporcular:
            row = self.sporcu_table.rowCount()
            self.sporcu_table.insertRow(row)
            self.sporcu_table.setItem(row, 0, QTableWidgetItem(str(s['sporcu_id'])))
            self.sporcu_table.setItem(row, 1, QTableWidgetItem(s['ad']))
            self.sporcu_table.setItem(row, 2, QTableWidgetItem(s['soyad']))
            self.sporcu_table.setItem(row, 3, QTableWidgetItem(str(s['yas'])))
            self.sporcu_table.setItem(row, 4, QTableWidgetItem(f"{s['kilo']} kg"))
            self.sporcu_table.setItem(row, 5, QTableWidgetItem(f"{s['boy']} cm"))
            self.sporcu_table.setItem(row, 6, QTableWidgetItem(s['cinsiyet']))
            self.sporcu_table.setItem(row, 7, QTableWidgetItem(s['hedef']))

    def sporcu_ekle(self):
        dialog = SporcuEkleDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.result:
            self.db.sporcu_ekle(*dialog.result)
            QMessageBox.information(self, "Başarılı", "✅ Sporcu başarıyla eklendi!")
            self.sporculari_listele()
            self.update_dashboard()
            self.stats_widget.update_charts()

    def sporcu_sil(self):
        row = self.sporcu_table.currentRow()
        if row >= 0:
            sporcu_id = int(self.sporcu_table.item(row, 0).text())
            sporcu_adi = f"{self.sporcu_table.item(row, 1).text()} {self.sporcu_table.item(row, 2).text()}"
            reply = QMessageBox.question(self, "Silme Onayı", f"'{sporcu_adi}' sporcusunu silmek istediğinize emin misiniz?",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.db.sporcu_sil(sporcu_id)
                QMessageBox.information(self, "Başarılı", "✅ Sporcu silindi!")
                self.sporculari_listele()
                self.takipleri_listele()
                self.update_dashboard()
                self.stats_widget.update_charts()
        else:
            QMessageBox.warning(self, "Uyarı", "Lütfen silinecek sporcuyu seçin!")

    def ilerleme_kaydet(self):
        row = self.sporcu_table.currentRow()
        if row >= 0:
            sporcu_id = int(self.sporcu_table.item(row, 0).text())
            sporcu_adi = f"{self.sporcu_table.item(row, 1).text()} {self.sporcu_table.item(row, 2).text()}"
            mevcut_kilo = float(self.sporcu_table.item(row, 4).text().replace(" kg", ""))

            dialog = IlerlemeKaydetDialog(sporcu_adi, mevcut_kilo, self)
            if dialog.exec_() == QDialog.Accepted:
                yeni_kilo = dialog.result
                self.db.ilerleme_kaydet(sporcu_id, yeni_kilo)
                QMessageBox.information(self, "Başarılı", f"✅ {sporcu_adi} için ilerleme kaydedildi!\n\n📉 Eski Kilo: {mevcut_kilo} kg\n📈 Yeni Kilo: {yeni_kilo} kg")
                self.sporculari_listele()
                self.update_dashboard()
                self.stats_widget.update_charts()
        else:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir sporcu seçin!")

    def ilerleme_grafigi(self):
        row = self.sporcu_table.currentRow()
        if row >= 0:
            sporcu_id = int(self.sporcu_table.item(row, 0).text())
            sporcu_adi = f"{self.sporcu_table.item(row, 1).text()} {self.sporcu_table.item(row, 2).text()}"

            ilerlemeler = self.db.ilerlemeleri_getir(sporcu_id)

            if len(ilerlemeler) < 2:
                QMessageBox.information(self, "Bilgi", "📊 Grafik görüntülemek için en az 2 ilerleme kaydı gereklidir.\n\nLütfen önce 'İlerleme Kaydet' butonu ile kilo takibi yapın.")
                return

            grafik_dialog = QDialog(self)
            grafik_dialog.setWindowTitle(f"📊 {sporcu_adi} - İlerleme Grafiği")
            grafik_dialog.setGeometry(200, 200, 800, 500)
            grafik_dialog.setStyleSheet("background-color: #1a1a2e; border-radius: 15px;")

            layout = QVBoxLayout()
            grafik_widget = IlerlemeGrafikWidget(self.db, grafik_dialog)
            grafik_widget.update_chart(sporcu_id)
            layout.addWidget(grafik_widget)

            kapat_btn = QPushButton("KAPAT")
            kapat_btn.setStyleSheet("background-color: #f5a623; color: #1a1a2e; padding: 12px; border-radius: 10px; font-weight: bold;")
            kapat_btn.clicked.connect(grafik_dialog.accept)
            layout.addWidget(kapat_btn)

            grafik_dialog.setLayout(layout)
            grafik_dialog.exec_()
        else:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir sporcu seçin!")

    def antrenmanlari_listele(self):
        antrenmanlar = self.db.antrenmanlari_getir()
        self.antrenman_table.setRowCount(0)
        for a in antrenmanlar:
            row = self.antrenman_table.rowCount()
            self.antrenman_table.insertRow(row)
            sure = f"{a['saat']}s {a['dakika']}dk" if a['saat'] > 0 else f"{a['dakika']}dk"
            self.antrenman_table.setItem(row, 0, QTableWidgetItem(str(a['antrenman_id'])))
            self.antrenman_table.setItem(row, 1, QTableWidgetItem(a['ad']))
            self.antrenman_table.setItem(row, 2, QTableWidgetItem(a['kategori']))
            self.antrenman_table.setItem(row, 3, QTableWidgetItem(sure))
            self.antrenman_table.setItem(row, 4, QTableWidgetItem(a['zorluk_seviyesi']))
            self.antrenman_table.setItem(row, 5, QTableWidgetItem(a['aciklama'][:40] + "..." if len(a['aciklama'] or '') > 40 else a['aciklama'] or ''))

    def antrenman_ekle(self):
        dialog = AntrenmanEkleDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.result:
            self.db.antrenman_ekle(*dialog.result)
            QMessageBox.information(self, "Başarılı", "✅ Antrenman başarıyla eklendi!")
            self.antrenmanlari_listele()
            self.update_dashboard()
            self.stats_widget.update_charts()

    def antrenman_sil(self):
        row = self.antrenman_table.currentRow()
        if row >= 0:
            antrenman_id = int(self.antrenman_table.item(row, 0).text())
            antrenman_adi = self.antrenman_table.item(row, 1).text()
            reply = QMessageBox.question(self, "Silme Onayı", f"'{antrenman_adi}' antrenmanını silmek istediğinize emin misiniz?",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.db.antrenman_sil(antrenman_id)
                QMessageBox.information(self, "Başarılı", "✅ Antrenman silindi!")
                self.antrenmanlari_listele()
                self.update_dashboard()
                self.stats_widget.update_charts()
        else:
            QMessageBox.warning(self, "Uyarı", "Lütfen silinecek antrenmanı seçin!")

    def takipleri_listele(self):
        takipler = self.db.takipler_getir()
        self.takip_table.setRowCount(0)
        for t in takipler:
            row = self.takip_table.rowCount()
            self.takip_table.insertRow(row)
            self.takip_table.setItem(row, 0, QTableWidgetItem(str(t['takip_id'])))
            self.takip_table.setItem(row, 1, QTableWidgetItem(f"{t['sporcu_ad']} {t['sporcu_soyad']}"))
            self.takip_table.setItem(row, 2, QTableWidgetItem(t['antrenman_ad']))
            self.takip_table.setItem(row, 3, QTableWidgetItem(f"{t['kalori']} kcal"))
            self.takip_table.setItem(row, 4, QTableWidgetItem(str(t['nabiz']) if t['nabiz'] else "-"))
            self.takip_table.setItem(row, 5, QTableWidgetItem(t['tarih'][:16]))
            self.takip_table.setItem(row, 6, QTableWidgetItem(t['notlar'][:40] + "..." if len(t['notlar'] or '') > 40 else t['notlar'] or ''))

    def takip_ekle(self):
        if not self.db.sporculari_getir():
            QMessageBox.warning(self, "Uyarı", "Önce sporcu ekleyin!")
            return
        if not self.db.antrenmanlari_getir():
            QMessageBox.warning(self, "Uyarı", "Önce antrenman ekleyin!")
            return

        dialog = TakipEkleDialog(self.db, self)
        if dialog.exec_() == QDialog.Accepted and dialog.result:
            self.db.takip_ekle(*dialog.result)
            QMessageBox.information(self, "Başarılı", "✅ Takip başarıyla oluşturuldu!")
            self.takipleri_listele()
            self.update_dashboard()
            self.stats_widget.update_charts()


# ===================== MAIN =====================

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = FitnessTakipUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
