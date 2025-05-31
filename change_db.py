import tkinter as tk
from tkinter import simpledialog, messagebox, Toplevel, ttk
from PIL import Image, ImageTk
import random
import sqlite3
from tkinter import scrolledtext
from collections import defaultdict
def create_tables(self):
    """필요한 테이블 생성 및 업그레이드"""
    tables = [
        """CREATE TABLE IF NOT EXISTS school_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_name TEXT NOT NULL,
            grade TEXT NOT NULL,
            class_num TEXT NOT NULL)""",
        """CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_name TEXT NOT NULL,
            grade TEXT NOT NULL,
            class_num TEXT NOT NULL,
            name TEXT NOT NULL,
            gender TEXT NOT NULL,
            eyestright TEXT NOT NULL,
            UNIQUE(school_name, grade, class_num, name))""",
        """CREATE TABLE IF NOT EXISTS last_layout (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_name TEXT NOT NULL,
            grade TEXT NOT NULL,
            class_num TEXT NOT NULL,
            name TEXT NOT NULL,
            gender TEXT NOT NULL,
            eyestright TEXT NOT NULL,
            row INTEGER NOT NULL,
            col INTEGER NOT NULL)""",
        """CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_name TEXT NOT NULL,
            grade TEXT NOT NULL,
            class_num TEXT NOT NULL,
            consider_eyesight INTEGER NOT NULL,
            separate_gender INTEGER NOT NULL,
            prevent_same_seat INTEGER NOT NULL DEFAULT 0,
            prevent_same_seat_count INTEGER NOT NULL DEFAULT 3)""",
        """CREATE TABLE IF NOT EXISTS seat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_name TEXT NOT NULL,
            grade TEXT NOT NULL,
            class_num TEXT NOT NULL,
            name TEXT NOT NULL,
            row INTEGER NOT NULL,
            col INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""
    ]
    
    # 기존 테이블 업그레이드 (컬럼 추가)
    upgrade_queries = [
        "ALTER TABLE settings ADD COLUMN prevent_same_seat INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE settings ADD COLUMN prevent_same_seat_count INTEGER NOT NULL DEFAULT 3"
    ]
    
    for table in tables:
        self.cursor.execute(table)
    
    # 기존 테이블에 컬럼 추가 시도 (이미 존재하면 무시됨)
    try:
        for query in upgrade_queries:
            self.cursor.execute(query)
    except sqlite3.OperationalError as e:
        if "duplicate column" not in str(e):
            raise e
    
    self.conn.commit()