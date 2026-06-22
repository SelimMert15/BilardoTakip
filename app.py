from flask import Flask, render_template, redirect, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Masa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    isim = db.Column(db.String(100), nullable=False)
    tip = db.Column(db.String(50), nullable=False)
    aktif = db.Column(db.Boolean, default=False)
    acilis_zamani = db.Column(db.DateTime, nullable=True)
class Urun(db.Model):
    id = db.Column(db.Integer, primary_key=True)

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
    id = db.Column(db.Integer, primary_key=True)

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
    id = db.Column(db.Integer, primary_key=True)

    urun_id = db.Column(
        db.Integer,
        db.ForeignKey("urun.id")
    )

    miktar = db.Column(db.Integer)

    aciklama = db.Column(
        db.String(200)
    )

    tarih = db.Column(
        db.DateTime,
        default=datetime.now
    )
@app.route("/")
def home():

    masalar = Masa.query.all()

    urunler = Urun.query.all()

    siparisler = Siparis.query.all()

    urun_dict = {}
    fiyat_dict = {}

    for urun in urunler:
        urun_dict[urun.id] = urun.isim
        fiyat_dict[urun.id] = urun.fiyat

    siparis_ozet = {}

    siparis_toplamlari = {}

    genel_toplamlar = {}

    for siparis in siparisler:

        if siparis.masa_id not in siparis_ozet:
            siparis_ozet[siparis.masa_id] = {}

        urun_adi = urun_dict[siparis.urun_id]

        if urun_adi not in siparis_ozet[siparis.masa_id]:

            siparis_ozet[siparis.masa_id][urun_adi] = {
                "adet": 0,
                "urun_id": siparis.urun_id
            }

        siparis_ozet[siparis.masa_id][urun_adi]["adet"] += siparis.adet

        if siparis.masa_id not in siparis_toplamlari:
            siparis_toplamlari[siparis.masa_id] = 0

        siparis_toplamlari[siparis.masa_id] += (
            fiyat_dict[siparis.urun_id]
            * siparis.adet
        )

    simdi = datetime.now()

    ucretler = {
        "3_bant": 300,
        "amerikan": 250,
        "langirt": 100,
        "masa_tenisi": 120
    }

    return render_template(
        "index.html",
        masalar=masalar,
        urunler=urunler,
        siparisler=siparisler,
        urun_dict=urun_dict,
        siparis_ozet=siparis_ozet,
        siparis_toplamlari=siparis_toplamlari,
        genel_toplamlar=genel_toplamlar,
        simdi=simdi,
        ucretler=ucretler
    )


@app.route("/masa_ac/<int:masa_id>")
def masa_ac(masa_id):

    masa = Masa.query.get(masa_id)

    if masa:
        masa.aktif = True
        masa.acilis_zamani = datetime.now()
        db.session.commit()

    return redirect("/")


@app.route("/masa_kapat/<int:masa_id>")
def masa_kapat(masa_id):

    masa = Masa.query.get(masa_id)

    if masa:
        masa.aktif = False
        masa.acilis_zamani = None
        db.session.commit()

    return redirect("/")


@app.route("/api/masa_ac/<int:masa_id>")
def api_masa_ac(masa_id):

    masa = Masa.query.get(masa_id)

    if masa:
        masa.aktif = True
        masa.acilis_zamani = datetime.now()
        db.session.commit()

    return jsonify({"success": True})

@app.route("/api/masa_kapat/<int:masa_id>")
def api_masa_kapat(masa_id):

    masa = Masa.query.get(masa_id)

    if masa:

        ucretler = {
            "3_bant": 300,
            "amerikan": 250,
            "langirt": 100,
            "masa_tenisi": 120
        }

        masa_ucreti = 0

        if masa.acilis_zamani:

            gecen_sure = (
                datetime.now()
                - masa.acilis_zamani
            ).total_seconds()

            masa_ucreti = (
                gecen_sure
                * ucretler[masa.tip]
            ) / 3600

        siparisler = Siparis.query.filter_by(
            masa_id=masa_id
        ).all()

        siparis_ucreti = 0

        for siparis in siparisler:

            urun = Urun.query.get(
                siparis.urun_id
            )

            siparis_ucreti += (
                urun.fiyat
                * siparis.adet
            )

        toplam_ucret = (
            masa_ucreti
            + siparis_ucreti
        )

        yeni_kayit = GelirKaydi(
            masa_adi=masa.isim,
            masa_ucreti=masa_ucreti,
            siparis_ucreti=siparis_ucreti,
            toplam_ucret=toplam_ucret
        )

        db.session.add(yeni_kayit)

        print("Bulunan siparis:", len(siparisler))

        for siparis in siparisler:
            db.session.delete(siparis)

        masa.aktif = False
        masa.acilis_zamani = None

        db.session.commit()

    return jsonify({"success": True})

@app.route("/api/siparis_arttir/<int:masa_id>/<int:urun_id>")
def siparis_arttir(masa_id, urun_id):

    siparis = Siparis.query.filter_by(
        masa_id=masa_id,
        urun_id=urun_id
    ).first()

    if siparis:

        siparis.adet += 1

        urun = Urun.query.get(urun_id)

        if urun and urun.stok_takibi:
            urun.stok -= 1

        db.session.commit()

    return jsonify({"success": True})


@app.route("/api/siparis_azalt/<int:masa_id>/<int:urun_id>")
def siparis_azalt(masa_id, urun_id):

    siparis = Siparis.query.filter_by(
        masa_id=masa_id,
        urun_id=urun_id
    ).first()

    if siparis:

        urun = Urun.query.get(urun_id)

        if urun and urun.stok_takibi:
            urun.stok += 1

        siparis.adet -= 1

        if siparis.adet <= 0:
            db.session.delete(siparis)

        db.session.commit()

    return jsonify({"success": True})


@app.route("/api/siparis_sil/<int:masa_id>/<int:urun_id>")
def siparis_sil(masa_id, urun_id):

    siparis = Siparis.query.filter_by(
        masa_id=masa_id,
        urun_id=urun_id
    ).first()

    if siparis:

        urun = Urun.query.get(urun_id)

        if urun and urun.stok_takibi:
            urun.stok += siparis.adet

        db.session.delete(siparis)

        db.session.commit()

    return jsonify({"success": True})

    if masa:

        siparisler = Siparis.query.filter_by(
            masa_id=masa_id
        ).all()

        print("Bulunan siparis:", len(siparisler))

        for siparis in siparisler:
            db.session.delete(siparis)

        masa.aktif = False
        masa.acilis_zamani = None

        db.session.commit()

    return jsonify({"success": True})

@app.route("/admin")
def admin():

    gelirler = GelirKaydi.query.all()

    simdi = datetime.now()

    bugun_gelirleri = [
        g for g in gelirler
        if g.tarih.date() == simdi.date()
    ]

    hafta_gelirleri = [
        g for g in gelirler
        if (simdi - g.tarih).days < 7
    ]

    ay_gelirleri = [
        g for g in gelirler
        if g.tarih.month == simdi.month
        and g.tarih.year == simdi.year
    ]

    bugun_toplam = sum(
        g.toplam_ucret
        for g in bugun_gelirleri
    )

    hafta_toplam = sum(
        g.toplam_ucret
        for g in hafta_gelirleri
    )

    ay_toplam = sum(
        g.toplam_ucret
        for g in ay_gelirleri
    )

    genel_toplam = sum(
        g.toplam_ucret
        for g in gelirler
    )

    masa_toplam = sum(
        g.masa_ucreti
        for g in gelirler
    )

    siparis_toplam = sum(
        g.siparis_ucreti
        for g in gelirler
    )

    return render_template(
        "admin.html",
        gelirler=gelirler,
        masa_toplam=masa_toplam,
        siparis_toplam=siparis_toplam,
        genel_toplam=genel_toplam,
        bugun_toplam=bugun_toplam,
        hafta_toplam=hafta_toplam,
        ay_toplam=ay_toplam
    )

@app.route("/siparis_ekle/<int:masa_id>/<int:urun_id>")
def siparis_ekle(masa_id, urun_id):

    yeni_siparis = Siparis(
        masa_id=masa_id,
        urun_id=urun_id,
        adet=1
    )

    db.session.add(yeni_siparis)

    db.session.commit()

    return redirect("/")
@app.route("/siparis_ekle_form", methods=["POST"])
def siparis_ekle_form():

    masa_id = request.form["masa_id"]
    urun_id = request.form["urun_id"]

    print("FORM VERISI:", request.form)

    adet = int(request.form.get("adet", 1))

    urun = Urun.query.get(urun_id)

    if urun and urun.stok_takibi:

        if urun.stok < adet:
            return redirect("/")

        urun.stok -= adet

    yeni_siparis = Siparis(
        masa_id=masa_id,
        urun_id=urun_id,
        adet=adet
    )

    db.session.add(yeni_siparis)

    db.session.commit()

    return redirect("/")
if __name__ == "__main__":

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

                masa = Masa(
                    isim=isim,
                    tip=tip
                )

                db.session.add(masa)

            db.session.commit()

        if Urun.query.count() == 0:

            varsayilan_urunler = [

                ("Sade Soda", 40, 24, True, 5),
                ("Meyveli Soda", 40, 24, True, 5),

                ("Büyük Su", 20, 48, True, 10),
                ("Küçük Su", 15, 48, True, 10),

                ("Çay", 20, None, False, None),
                ("Türk Kahvesi", 80, None, False, None),

                ("Kaşarli Tost", 100, None, False, None),
                ("Karişik Tost", 120, None, False, None)

            ]

            for isim, fiyat, stok, stok_takibi, minimum_stok in varsayilan_urunler:

                urun = Urun(
                    isim=isim,
                    fiyat=fiyat,
                    stok=stok,
                    stok_takibi=stok_takibi,
                    minimum_stok=minimum_stok
                )

                db.session.add(urun)

            db.session.commit()
    app.run(debug=True)