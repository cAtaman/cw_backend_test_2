import typing as t
import requests
from datetime import datetime

from .models import Book
from .models import BookSchema
from .models import Borrow
from .models import BorrowSchema
from .models import User
from .models import UserSchema
from .wsgi import db
from ..constants import CLIENT_PORT, CLIENT_HOST, SECRET_KEY


def get_books(available: bool = None) -> t.Tuple[t.List[dict], int]:
    if available is None:
        books = Book.query.filter_by().all()
        books_dict = BookSchema(many=True).dump(books)
        return books_dict, 200

    books_dict = BookSchema(many=True).dump(Book.query.filter_by(available=available).all())
    # attach return date if getting unavailable books
    if not available:
        all_borrows = Borrow.query.filter(Borrow.return_date >= datetime.now().date()).all()
        all_borrows = BorrowSchema(many=True).dump(all_borrows)
        borrows_by_book = {}
        for borrow in all_borrows:
            br = borrows_by_book.get(borrow["book_id"], [])
            borrows_by_book[borrow["book_id"]] = br.append(borrow)

        for book in books_dict:
            borrows = borrows_by_book.get(book["book_id"])
            book["return_date"] = borrows["return_date"]
    return books_dict, 200


def add_book(book_data: dict) -> t.Tuple[dict, int]:
    new_book_dict = {
        "name": book_data.get("name"),
        "author": book_data.get("author"),
        "publisher": book_data.get("publisher"),
        "category": book_data.get("category"),
        "available": book_data.get("available")
    }
    book = BookSchema().load(new_book_dict)
    db.session.add(book)
    db.session.commit()
    client_handler = ClientAPICallHandler(CLIENT_HOST, CLIENT_PORT)
    client_handler.add_book(book_data)
    return BookSchema().dump(book), 200


def remove_book(book_id: int) -> t.Tuple[str, int]:
    book = Book.query.filter_by(book_id=book_id).first()
    if book:
        client_handler = ClientAPICallHandler(CLIENT_HOST, CLIENT_PORT)
        client_handler.remove_book(book_id)
        db.session.delete(book)
        db.session.commit()
        return "Book removed successfully", 200
    else:
        return "Book was not in catalogue", 400


def get_users(with_borrows: bool = False):
    all_users = UserSchema(many=True).dump(User.query.all())
    if with_borrows:
        all_borrows = BorrowSchema(many=True).dump(Borrow.query.all())
        borrows_by_user = {}
        for borrow in all_borrows:
            br = borrows_by_user.get(borrow["user_id"], [])
            borrows_by_user[borrow["user_id"]] = br + [borrow]

        for user in all_users:
            borrows = borrows_by_user.get(user["user_id"], [])
            borrowed_book_ids = [b["book_id"] for b in borrows]
            user["books_borrowed"] = list(map(
                lambda x: BookSchema().dump(Book.query.filter_by(book_id=x).first()),
                borrowed_book_ids
            ))
            user.pop("password")
    return all_users, 200


class ClientAPICallHandler:
    """Handles internal calls to Client API"""
    host: str
    port: str
    scheme: str = "http"

    def __init__(self, host, port, scheme=None):
        self.host = host
        self.port = port
        self.scheme = scheme or self.scheme
        self.headers = {"secret": SECRET_KEY}
        self.base_url = f"{self.scheme}://{self.host}:{self.port}/"

    def remove_book(self, book_id: int):
        url = self.base_url + "books"
        resp = requests.delete(url, params={"book_id": book_id})
        return resp.status_code

    def add_book(self, book_data: dict):
        url = self.base_url + "books"
        resp = requests.post(url, json=book_data)
        return resp.status_code
