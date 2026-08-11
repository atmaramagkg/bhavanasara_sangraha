// screens/bookmarks_screen.dart
import 'package:flutter/material.dart';
import '../app_theme.dart';
import '../services/app_settings.dart';
import '../services/bss_repository.dart';
import '../services/translations.dart';

/// Lists every bookmarked lila section. Tapping one returns its section id
/// to the caller (the reading screen), which scrolls to it.
class BookmarksScreen extends StatelessWidget {
  final BssRepository repository;

  const BookmarksScreen({super.key, required this.repository});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final goldColor = isDark ? BssColors.darkOakGold : BssColors.goldAccent;
    final textColor = isDark ? BssColors.darkOakText : BssColors.darkText;
    final subTextCol = isDark ? BssColors.darkOakSubText : BssColors.subText;

    return Scaffold(
      appBar: AppBar(title: Text(Translations.t('menu.bookmarks'))),
      body: ValueListenableBuilder<Set<int>>(
        valueListenable: AppSettings.bookmarkedSectionIds,
        builder: (context, bookmarkedIds, _) {
          if (bookmarkedIds.isEmpty) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text(
                  Translations.t('screen.bookmarks.empty'),
                  textAlign: TextAlign.center,
                  style: TextStyle(color: subTextCol),
                ),
              ),
            );
          }

          return FutureBuilder<List<ContinuousReadingItem>>(
            future: repository.getSectionsByIds(bookmarkedIds.toList()),
            builder: (context, snapshot) {
              if (snapshot.connectionState == ConnectionState.waiting) {
                return const Center(child: CircularProgressIndicator());
              }
              final items = snapshot.data ?? const [];

              return ListView.separated(
                padding: const EdgeInsets.symmetric(vertical: 8),
                itemCount: items.length,
                separatorBuilder: (_, _) => Divider(height: 1, color: goldColor.withAlpha(60)),
                itemBuilder: (context, index) {
                  final item = items[index];
                  return ListTile(
                    leading: Icon(Icons.bookmark, color: goldColor),
                    title: Text(
                      item.section.title,
                      style: TextStyle(fontWeight: FontWeight.w600, color: textColor),
                    ),
                    subtitle: Text(
                      '${item.mainPeriod.title} · ${item.subPeriod.timeRange}',
                      style: TextStyle(fontSize: 12, color: subTextCol),
                    ),
                    trailing: IconButton(
                      icon: const Icon(Icons.close, size: 18),
                      tooltip: Translations.t('common.bookmark.remove'),
                      onPressed: () => AppSettings.toggleBookmark(item.section.id),
                    ),
                    onTap: () => Navigator.of(context).pop(item.section.id),
                  );
                },
              );
            },
          );
        },
      ),
    );
  }
}
