// screens/books_screen.dart
import 'package:flutter/material.dart';
import '../app_theme.dart';
import '../models/book.dart';
import '../services/bss_repository.dart';

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
      appBar: AppBar(title: const Text('Scriptures Quoted')),
      body: FutureBuilder<List<Book>>(
        future: repository.getAllBooks(),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          final books = snapshot.data ?? const [];
          if (books.isEmpty) {
            return const Center(child: Text('No scriptures found.'));
          }

          return ListView.separated(
            padding: const EdgeInsets.symmetric(vertical: 8),
            itemCount: books.length,
            separatorBuilder: (_, _) => Divider(height: 1, color: goldColor.withAlpha(60)),
            itemBuilder: (context, index) {
              final Book b = books[index];
              return ListTile(
                title: Text(
                  b.title,
                  style: TextStyle(fontFamily: 'NotoSerif', fontWeight: FontWeight.w600, color: textColor),
                ),
                subtitle: b.author.isNotEmpty ? Text(b.author, style: TextStyle(color: subTextCol)) : null,
                trailing: b.quoteCount > 0
                    ? Text(
                        '${b.quoteCount} quote${b.quoteCount == 1 ? '' : 's'}',
                        style: TextStyle(fontSize: 12, color: goldColor),
                      )
                    : null,
              );
            },
          );
        },
      ),
    );
  }
}
