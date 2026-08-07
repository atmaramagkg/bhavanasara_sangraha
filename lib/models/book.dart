// models/book.dart
class Book {
  final int id;
  final String slug;
  final String title;
  final String author;
  final int quoteCount;

  const Book({
    required this.id,
    required this.slug,
    required this.title,
    required this.author,
    this.quoteCount = 0,
  });
}
