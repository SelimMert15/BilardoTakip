from flask import Flask, render_template, redirect, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

database_url = os.getenv("DATABASE_URL")

if database_url:
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ==========================
# MODELLER
# ==========================

class Masa(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    isim = db.Column(
        db.String(100),
        nullable=False
    )

    tip = db.Column(
        db.String(50),
        nullable=False
    )

    aktif = db.Column(
        db.Boolean,
        default=False
    )

    acilis_zamani = db.Column(
        db.DateTime,
        nullable=True
    )


class Urun(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    isim = db.Column(
        db.String(100),
        nullable=False
    )

    fiyat = db.Column(
        db.Float,
        nullable=False
    )

    stok = db.Column(
        db.Integer,
        nullable=True
    )

    stok_takibi = db.Column(
        db.Boolean,
        default=True
    )

    minimum_stok = db.Column(
        db.Integer,
        nullable=True
    )

    aktif = db.Column(
        db.Boolean,
        default=True
    )

class Siparis(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    masa_id = db.Column(
        db.Integer,
        db.ForeignKey("masa.id")
    )

    urun_id = db.Column(
        db.Integer,
        db.ForeignKey("urun.id")
    )

    adet = db.Column(
        db.Integer,
        default=1
    )

    zaman = db.Column(
        db.DateTime,
        default=datetime.now
    )


class GelirKaydi(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    tarih = db.Column(
        db.DateTime,
        default=datetime.now
    )

    masa_adi = db.Column(
        db.String(100)
    )

    masa_ucreti = db.Column(
        db.Float,
        default=0
    )

    siparis_ucreti = db.Column(
        db.Float,
        default=0
    )

    toplam_ucret = db.Column(
        db.Float,
        default=0
    )


class StokHareket(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    urun_id = db.Column(
        db.Integer,
        db.ForeignKey("urun.id")
    )

    miktar = db.Column(
        db.Integer
    )

    aciklama = db.Column(
        db.String(200)
    )

    tarih = db.Column(
        db.DateTime,
        default=datetime.now
    )
    
    # ==========================
# VERITABANI KURULUMU
# ==========================

with app.app_context():

    db.create_all()

    if Masa.query.count() == 0:

        varsayilan_masalar = [

            ("3 Bant 1", "3_bant"),
            ("3 Bant 2", "3_bant"),
            ("3 Bant 3", "3_bant"),

            ("Amerikan 1", "amerikan"),
            ("Amerikan 2", "amerikan"),

            ("Langirt", "langirt"),

            ("Masa Tenisi 1", "masa_tenisi"),
            ("Masa Tenisi 2", "masa_tenisi")

        ]

        for isim, tip in varsayilan_masalar:

            db.session.add(
                Masa(
                    isim=isim,
                    tip=tip
                )
            )

        db.session.commit()

    if Urun.query.count() == 0:

        varsayilan_urunler = [

            ("Sade Soda", 40, 24, True, 5),
            ("Meyveli Soda", 40, 24, True, 5),

            ("Büyük Su", 20, 48, True, 10),
            ("Küçük Su", 15, 48, True, 10),

            ("Çay", 20, None, False, None),
            ("Türk Kahvesi", 80, None, False, None),

            ("Kaşarlı Tost", 100, None, False, None),
            ("Karışık Tost", 120, None, False, None)

        ]

        for isim, fiyat, stok, stok_takibi, minimum_stok in varsayilan_urunler:

            db.session.add(
                Urun(
                    isim=isim,
                    fiyat=fiyat,
                    stok=stok,
                    stok_takibi=stok_takibi,
                    minimum_stok=minimum_stok
                )
            )

        db.session.commit()


# ==========================
# SABIT FIYATLAR
# ==========================

UCRETLER = {

    "3_bant": 300,
    "amerikan": 250,
    "langirt": 100,
    "masa_tenisi": 120

}

# ==========================
# ANA SAYFA
# ==========================

@app.route("/")
def home():

    masalar = Masa.query.all()

    urunler = Urun.query.order_by(
        Urun.isim
    ).all()

    siparisler = Siparis.query.all()

    urun_dict = {}
    fiyat_dict = {}

    for urun in urunler:

        urun_dict[urun.id] = urun.isim
        fiyat_dict[urun.id] = urun.fiyat

    siparis_ozet = {}
    siparis_toplamlari = {}

    for siparis in siparisler:

        if siparis.masa_id not in siparis_ozet:
            siparis_ozet[siparis.masa_id] = {}

        urun_adi = urun_dict.get(
            siparis.urun_id,
            "Silinmiş Ürün"
        )

        if urun_adi not in siparis_ozet[siparis.masa_id]:

            siparis_ozet[siparis.masa_id][urun_adi] = {
                "adet": 0,
                "urun_id": siparis.urun_id
            }

        siparis_ozet[siparis.masa_id][urun_adi]["adet"] += siparis.adet

        if siparis.masa_id not in siparis_toplamlari:
            siparis_toplamlari[siparis.masa_id] = 0

        siparis_toplamlari[siparis.masa_id] += (
            fiyat_dict.get(
                siparis.urun_id,
                0
            )
            * siparis.adet
        )

    return render_template(
        "index.html",
        masalar=masalar,
        urunler=urunler,
        siparisler=siparisler,
        urun_dict=urun_dict,
        siparis_ozet=siparis_ozet,
        siparis_toplamlari=siparis_toplamlari,
        genel_toplamlar={},
        simdi=datetime.now(),
        ucretler=UCRETLER
    )

# ==========================
# ADMIN PANELI
# ==========================

@app.route("/admin")
def admin():

    gelirler = GelirKaydi.query.order_by(
        GelirKaydi.tarih.desc()
    ).all()

    simdi = datetime.now()

    bugun_toplam = sum(
        g.toplam_ucret
        for g in gelirler
        if g.tarih.date() == simdi.date()
    )

    hafta_toplam = sum(
        g.toplam_ucret
        for g in gelirler
        if (simdi - g.tarih).days < 7
    )

    ay_toplam = sum(
        g.toplam_ucret
        for g in gelirler
        if g.tarih.month == simdi.month
        and g.tarih.year == simdi.year
    )

    masa_toplam = sum(
        g.masa_ucreti
        for g in gelirler
    )

    siparis_toplam = sum(
        g.siparis_ucreti
        for g in gelirler
    )

    genel_toplam = sum(
        g.toplam_ucret
        for g in gelirler
    )

    urunler = Urun.query.order_by(
        Urun.isim
    ).all()

    return render_template(
        "admin.html",
        gelirler=gelirler,
        urunler=urunler,
        bugun_toplam=bugun_toplam,
        hafta_toplam=hafta_toplam,
        ay_toplam=ay_toplam,
        masa_toplam=masa_toplam,
        siparis_toplam=siparis_toplam,
        genel_toplam=genel_toplam
    )

# ==========================
# STOK GUNCELLE
# ==========================

@app.route(
    "/stok_guncelle/<int:urun_id>",
    methods=["POST"]
)
def stok_guncelle(urun_id):

    urun = Urun.query.get_or_404(
        urun_id
    )

    try:

        yeni_stok = request.form.get(
            "stok"
        )

        yeni_fiyat = request.form.get(
            "fiyat"
        )

        if yeni_stok != "":
            urun.stok = int(yeni_stok)

        urun.fiyat = float(
            yeni_fiyat
        )

        db.session.commit()

    except Exception:

        db.session.rollback()

    return redirect("/admin")

# ==========================
# TOPLU STOK KAYDET
# ==========================

@app.route(
    "/toplu_stok_kaydet",
    methods=["POST"]
)
def toplu_stok_kaydet():

    urunler = Urun.query.all()

    for urun in urunler:

        stok = request.form.get(
            f"stok_{urun.id}"
        )

        fiyat = request.form.get(
            f"fiyat_{urun.id}"
        )

        takip = request.form.get(
            f"takip_{urun.id}"
        )

        if stok != "" and stok is not None:
            urun.stok = int(stok)

        if fiyat:
            urun.fiyat = float(fiyat)

        urun.stok_takibi = (
            takip == "on"
        )

        if not urun.stok_takibi:
            urun.stok = None

    db.session.commit()

    return redirect("/admin")


# ==========================
# YENI URUN EKLE
# ==========================

@app.route(
    "/urun_ekle",
    methods=["POST"]
)
def urun_ekle():

    isim = request.form.get(
        "isim"
    )

    fiyat = float(
        request.form.get(
            "fiyat",
            0
        )
    )

    stok_takibi = (
        request.form.get(
            "stok_takibi"
        ) == "on"
    )

    stok = request.form.get(
        "stok"
    )

    yeni_urun = Urun(
        isim=isim,
        fiyat=fiyat,
        stok=int(stok) if stok_takibi and stok else 0,
        stok_takibi=stok_takibi,
        minimum_stok=0
    )

    db.session.add(
        yeni_urun
    )

    db.session.commit()

    return redirect("/admin")

# ==========================
# CIRO SIFIRLA
# ==========================

@app.route("/ciro_sifirla_12345")
def ciro_sifirla():

    GelirKaydi.query.delete()

    db.session.commit()

    return "Tum ciro kayitlari silindi."

@app.route("/masa_isimlerini_guncelle")
def masa_isimlerini_guncelle():

    masa1 = Masa.query.filter_by(isim="3 Bant 1").first()
    masa2 = Masa.query.filter_by(isim="3 Bant 2").first()
    masa3 = Masa.query.filter_by(isim="3 Bant 3").first()

    if masa1:
        masa1.isim = "Zeki Masa"

    if masa2:
        masa2.isim = "Platin Masa"

    if masa3:
        masa3.isim = "Eyüp Mert'in Masası"

    db.session.commit()

    return "Masa isimleri guncellendi."

# ==========================
# MASA AC
# ==========================

@app.route("/api/masa_ac/<int:masa_id>")
def api_masa_ac(masa_id):

    masa = Masa.query.get_or_404(
        masa_id
    )

    if not masa.aktif:

        masa.aktif = True
        masa.acilis_zamani = datetime.now()

        db.session.commit()

    return jsonify({
        "success": True
    })


# ==========================
# MASA KAPAT
# ==========================

@app.route("/api/masa_kapat/<int:masa_id>")
def api_masa_kapat(masa_id):

    masa = Masa.query.get_or_404(
        masa_id
    )

    masa_ucreti = 0

    if masa.acilis_zamani:

        gecen_sure = (
            datetime.now()
            - masa.acilis_zamani
        ).total_seconds()

        masa_ucreti = (
            gecen_sure
            * UCRETLER[masa.tip]
        ) / 3600

    siparisler = Siparis.query.filter_by(
        masa_id=masa_id
    ).all()

    siparis_ucreti = 0

    for siparis in siparisler:

        urun = Urun.query.get(
            siparis.urun_id
        )

        if urun:

            siparis_ucreti += (
                urun.fiyat
                * siparis.adet
            )

    toplam_ucret = (
        masa_ucreti
        + siparis_ucreti
    )

    db.session.add(
        GelirKaydi(
            masa_adi=masa.isim,
            masa_ucreti=masa_ucreti,
            siparis_ucreti=siparis_ucreti,
            toplam_ucret=toplam_ucret
        )
    )

    for siparis in siparisler:
        db.session.delete(siparis)

    masa.aktif = False
    masa.acilis_zamani = None

    db.session.commit()

    return jsonify({
        "success": True
    })


# ==========================
# SIPARIS EKLE
# ==========================

@app.route(
    "/siparis_ekle_form",
    methods=["POST"]
)
def siparis_ekle_form():

    masa_id = int(
        request.form["masa_id"]
    )

    urun_id = int(
        request.form["urun_id"]
    )

    adet = int(
        request.form.get(
            "adet",
            1
        )
    )

    urun = Urun.query.get_or_404(
        urun_id
    )

    if urun.stok_takibi:

        if urun.stok is None:
            urun.stok = 0

        if urun.stok < adet:

            return redirect("/")

        urun.stok -= adet

    siparis = Siparis.query.filter_by(
        masa_id=masa_id,
        urun_id=urun_id
    ).first()

    if siparis:

        siparis.adet += adet

    else:

        db.session.add(
            Siparis(
                masa_id=masa_id,
                urun_id=urun_id,
                adet=adet
            )
        )

    db.session.commit()

    return redirect("/")


# ==========================
# SIPARIS ARTTIR
# ==========================

@app.route(
    "/api/siparis_arttir/<int:masa_id>/<int:urun_id>"
)
def siparis_arttir(
    masa_id,
    urun_id
):

    siparis = Siparis.query.filter_by(
        masa_id=masa_id,
        urun_id=urun_id
    ).first()

    urun = Urun.query.get_or_404(
        urun_id
    )

    if siparis:

        if urun.stok_takibi:

            if urun.stok is None:
                urun.stok = 0

            if urun.stok <= 0:

                return jsonify({
                    "success": False
                })

            urun.stok -= 1

        siparis.adet += 1

        db.session.commit()

    return jsonify({
        "success": True
    })


# ==========================
# SIPARIS AZALT
# ==========================

@app.route(
    "/api/siparis_azalt/<int:masa_id>/<int:urun_id>"
)
def siparis_azalt(
    masa_id,
    urun_id
):

    siparis = Siparis.query.filter_by(
        masa_id=masa_id,
        urun_id=urun_id
    ).first()

    if not siparis:

        return jsonify({
            "success": False
        })

    urun = Urun.query.get(
        urun_id
    )

    if urun and urun.stok_takibi:

        if urun.stok is None:
            urun.stok = 0

        urun.stok += 1

    siparis.adet -= 1

    if siparis.adet <= 0:

        db.session.delete(
            siparis
        )

    db.session.commit()

    return jsonify({
        "success": True
    })


# ==========================
# SIPARIS SIL
# ==========================

@app.route(
    "/api/siparis_sil/<int:masa_id>/<int:urun_id>"
)
def siparis_sil(
    masa_id,
    urun_id
):

    siparis = Siparis.query.filter_by(
        masa_id=masa_id,
        urun_id=urun_id
    ).first()

    if not siparis:

        return jsonify({
            "success": False
        })

    urun = Urun.query.get(
        urun_id
    )

    if urun and urun.stok_takibi:

        if urun.stok is None:
            urun.stok = 0

        urun.stok += siparis.adet

    db.session.delete(
        siparis
    )

    db.session.commit()

    return jsonify({
        "success": True
    })

# ==========================
# UYGULAMA BASLAT
# ==========================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )