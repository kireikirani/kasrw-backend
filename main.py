from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import date
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Kas RW API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


# ======================
# MODEL
# ======================

class TransaksiBase(BaseModel):
    tanggal: date
    keterangan: str
    tipe: str
    jumlah: float


class TransaksiUpdate(BaseModel):
    tanggal: Optional[date] = None
    keterangan: Optional[str] = None
    tipe: Optional[str] = None
    jumlah: Optional[float] = None


# ======================
# ROOT
# ======================

@app.get("/")
def root():
    return {"message": "Kas RW API berjalan"}


# ======================
# GET ALL
# ======================

@app.get("/transaksi")
def get_all():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            id,
            tanggal,
            keterangan,
            tipe,
            jumlah
        FROM kas_transaksi
        ORDER BY tanggal DESC
    """)

    rows = cursor.fetchall()

    cursor.close()
    db.close()

    return rows


# ======================
# GET BY ID
# ======================

@app.get("/transaksi/{id}")
def get_one(id: int):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM kas_transaksi
        WHERE id = %s
        """,
        (id,)
    )

    row = cursor.fetchone()

    cursor.close()
    db.close()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Transaksi tidak ditemukan"
        )

    return row


# ======================
# CREATE
# ======================

@app.post("/transaksi", status_code=201)
def create(data: TransaksiBase):

    if data.tipe not in ["masuk", "keluar"]:
        raise HTTPException(
            status_code=400,
            detail="tipe harus 'masuk' atau 'keluar'"
        )

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO kas_transaksi
        (tanggal, keterangan, tipe, jumlah)
        VALUES (%s, %s, %s, %s)
        """,
        (
            data.tanggal,
            data.keterangan,
            data.tipe,
            data.jumlah,
        ),
    )

    db.commit()

    new_id = cursor.lastrowid

    cursor.close()
    db.close()

    return {
        "id": new_id,
        "message": "Transaksi berhasil ditambahkan"
    }


# ======================
# UPDATE
# ======================

@app.put("/transaksi/{id}")
def update(id: int, data: TransaksiUpdate):

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM kas_transaksi
        WHERE id = %s
        """,
        (id,)
    )

    row = cursor.fetchone()

    if not row:
        cursor.close()
        db.close()

        raise HTTPException(
            status_code=404,
            detail="Transaksi tidak ditemukan"
        )

    updated = {
        **row,
        **{
            k: v
            for k, v in data.model_dump().items()
            if v is not None
        }
    }

    if updated["tipe"] not in ["masuk", "keluar"]:
        raise HTTPException(
            status_code=400,
            detail="tipe harus 'masuk' atau 'keluar'"
        )

    cursor.execute(
        """
        UPDATE kas_transaksi
        SET
            tanggal = %s,
            keterangan = %s,
            tipe = %s,
            jumlah = %s
        WHERE id = %s
        """,
        (
            updated["tanggal"],
            updated["keterangan"],
            updated["tipe"],
            updated["jumlah"],
            id
        )
    )

    db.commit()

    cursor.close()
    db.close()

    return {
        "message": "Transaksi berhasil diperbarui"
    }


# ======================
# DELETE
# ======================

@app.delete("/transaksi/{id}")
def delete(id: int):

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        DELETE FROM kas_transaksi
        WHERE id = %s
        """,
        (id,)
    )

    db.commit()

    affected = cursor.rowcount

    cursor.close()
    db.close()

    if affected == 0:
        raise HTTPException(
            status_code=404,
            detail="Transaksi tidak ditemukan"
        )

    return {
        "message": "Transaksi berhasil dihapus"
    }