// screens/books_screen.dart
import 'package:flutter/material.dart';
import '../app_theme.dart';
import '../models/book.dart';
import '../services/bss_repository.dart';
import '../services/translations.dart';
import 'book_reader_screen.dart';

/// All source scriptures this compilation quotes from.
class BooksScreen extends StatelessWidget {
  final BssRepository repository;

  const BooksScreen({super.key, required this.repository});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final goldColor = isDark ? BssColors.darkOakGold : BssColors.goldAccent;
    final textColor = isDark ? BssColors.darkOakText : BssColors.darkText;
    final subTextCol = isDark ? BssColors.darkOakSubText : BssColors.subText;

    return Scaffold(
      appBar: AppBar(title: Text(Translations.t('screen.books.title'))),
      body: FutureBuilder<List<Book>>(
        future: repository.getAllBooks(),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          final books = snapshot.data ?? const [];
          if (books.isEmpty) {
            return Center(child: Text(Translations.t('screen.books.empty')));
          }

          return SafeArea(
            top: false,
            child: ListView.separated(
              padding: const EdgeInsets.symmetric(vertical: 8),
              itemCount: books.length,
              separatorBuilder: (_, _) => Divider(height: 1, color: goldColor.withAlpha(60)),
              itemBuilder: (context, index) {
                final Book b = books[index];
                return ListTile(
                  title: Text(
                    b.title,
                    style: TextStyle(fontWeight: FontWeight.w600, color: textColor),
                  ),
                  subtitle: b.author.isNotEmpty ? Text(b.author, style: TextStyle(color: subTextCol)) : null,
                  trailing: b.quoteCount > 0
                      ? Text(
                          '${b.quoteCount} ${Translations.plural('common.quote', b.quoteCount)}',
                          style: TextStyle(fontSize: 12, color: goldColor),
                        )
                      : null,
                  onTap: () => Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => BookReaderScreen(repository: repository, book: b),
                    ),
                  ),
                );
              },
            ),
          );
        },
      ),
    );
  }
}
