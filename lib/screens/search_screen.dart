// screens/search_screen.dart
import 'package:flutter/material.dart';
import '../app_theme.dart';
import '../services/app_settings.dart';
import '../services/bss_repository.dart';
import '../services/translations.dart';
import '../utils/text_utils.dart';

class SearchResult {
  final int sectionId;
  final int? verseId;
  final String query;

  const SearchResult({required this.sectionId, this.verseId, required this.query});
}

class _SearchHit {
  final ContinuousReadingItem item;
  final VerseDetail? verse; // null when only the section title matched
  final int matchStart; // index into the *displayed* text, for highlighting
  final int matchLength;
  final bool matchedInVerse;

  const _SearchHit({
    required this.item,
    required this.verse,
    required this.matchStart,
    required this.matchLength,
    required this.matchedInVerse,
  });
}

/// Simple, fully in-memory, diacritic-insensitive search over everything
/// already loaded for the reading feed.
class SearchScreen extends StatefulWidget {
  final List<ContinuousReadingItem> feedItems;
  final String initialQuery;

  const SearchScreen({
    super.key,
    required this.feedItems,
    this.initialQuery = '',
  });

  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  late final TextEditingController _controller =
      TextEditingController(text: widget.initialQuery);
  List<_SearchHit> _results = const [];
  bool _searched = false;

  @override
  void initState() {
    super.initState();
    if (widget.initialQuery.trim().isNotEmpty) {
      _performSearch();
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _onTextChanged(String rawQuery) {
    setState(() {
      _searched = false;
      _results = const [];
    });
  }

  void _performSearch() {
    final String query = normalizeForSearch(_controller.text.trim());
    if (query.isEmpty) {
      setState(() {
        _searched = false;
        _results = const [];
      });
      return;
    }

    final String langCode = AppSettings.locale.value.languageCode;
    final List<_SearchHit> quoteMatches = [];
    final List<_SearchHit> titleOnlyMatches = [];

    for (final item in widget.feedItems) {
      bool sectionTitleMatched =
          normalizeForSearch(item.section.title).contains(query);

      bool anyVerseMatched = false;
      for (final verse in item.verses) {
        String translationText = verse.translationForCode(langCode);
        if (translationText.isEmpty && verse.transliteration.isNotEmpty) {
          translationText = verse.transliteration;
        }
        final String normalizedVerse = normalizeForSearch(translationText);
        final int idx = normalizedVerse.indexOf(query);
        if (idx != -1) {
          anyVerseMatched = true;
          quoteMatches.add(_SearchHit(
            item: item,
            verse: verse,
            matchStart: idx,
            matchLength: query.length,
            matchedInVerse: true,
          ));
          continue;
        }

        final String normalizedRef = normalizeForSearch(verse.refDisplay);
        if (normalizedRef.contains(query)) {
          anyVerseMatched = true;
          quoteMatches.add(_SearchHit(
            item: item,
            verse: verse,
            matchStart: 0,
            matchLength: 0,
            matchedInVerse: false,
          ));
        }
      }

      if (sectionTitleMatched && !anyVerseMatched) {
        titleOnlyMatches.add(_SearchHit(
          item: item,
          verse: null,
          matchStart: 0,
          matchLength: 0,
          matchedInVerse: false,
        ));
      }
    }

    setState(() {
      _searched = true;
      _results = [...quoteMatches, ...titleOnlyMatches];
    });
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final goldColor = isDark ? BssColors.darkOakGold : BssColors.goldAccent;
    final textColor = isDark ? BssColors.darkOakText : BssColors.darkText;
    final subTextCol = isDark ? BssColors.darkOakSubText : BssColors.subText;

    return Scaffold(
      appBar: AppBar(
        title: TextField(
          controller: _controller,
          autofocus: true,
          onChanged: _onTextChanged,
          onSubmitted: (_) => _performSearch(),
          style: TextStyle(color: textColor),
          decoration: InputDecoration(
            hintText: Translations.t('screen.search.hint'),
            hintStyle: TextStyle(color: subTextCol),
            border: InputBorder.none,
          ),
        ),
        actions: [
          TextButton(
            onPressed: _performSearch,
            child: Text(Translations.t('screen.search.submit')),
          ),
          if (_controller.text.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.close),
              onPressed: () {
                _controller.clear();
                _onTextChanged('');
              },
            ),
        ],
      ),
      body: _buildBody(context, goldColor, textColor, subTextCol),
    );
  }

  Widget _buildBody(BuildContext context, Color goldColor, Color textColor, Color subTextCol) {
    if (!_searched) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(
            Translations.t('screen.search.empty'),
            textAlign: TextAlign.center,
            style: TextStyle(color: subTextCol),
          ),
        ),
      );
    }

    if (_results.isEmpty) {
      return Center(
        child: Text(
          Translations.t('screen.search.noResults'),
          style: TextStyle(color: subTextCol),
        ),
      );
    }

    return SafeArea(
      top: false,
      child: ListView.separated(
        padding: const EdgeInsets.symmetric(vertical: 8),
        itemCount: _results.length,
        separatorBuilder: (_, _) => Divider(height: 1, color: goldColor.withAlpha(60)),
        itemBuilder: (context, index) {
          final hit = _results[index];
          return InkWell(
            onTap: () => Navigator.of(context).pop(
              SearchResult(
                sectionId: hit.item.section.id,
                verseId: hit.verse?.verseId,
                query: _controller.text,
              ),
            ),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (hit.verse != null && hit.verse!.refDisplay.isNotEmpty)
                    Text(
                      hit.verse!.refDisplay,
                      style: TextStyle(fontSize: 11, color: goldColor, fontStyle: FontStyle.italic),
                    ),
                  if (hit.verse != null && hit.verse!.refDisplay.isNotEmpty)
                    const SizedBox(height: 3),
                  Text(
                    hit.item.section.title,
                    style: TextStyle(fontWeight: FontWeight.w600, fontSize: 15, color: textColor),
                  ),
                  const SizedBox(height: 4),
                  _buildSnippet(hit, subTextCol, goldColor),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildSnippet(_SearchHit hit, Color subTextCol, Color goldColor) {
    if (hit.verse == null) {
      return Text(
        '${hit.item.mainPeriod.title} · ${hit.item.subPeriod.timeRange}',
        style: TextStyle(fontSize: 12, color: subTextCol),
      );
    }

    final String langCode = AppSettings.locale.value.languageCode;
    String full = hit.verse!.translationForCode(langCode);
    if (full.isEmpty && hit.verse!.transliteration.isNotEmpty) {
      full = hit.verse!.transliteration;
    }

    if (!hit.matchedInVerse) {
      final String preview = full.length > 120
          ? '${full.substring(0, 120)}…'
          : full;
      return Text(
        preview,
        maxLines: 2,
        overflow: TextOverflow.ellipsis,
        style: TextStyle(fontSize: 13, color: subTextCol),
      );
    }

    const int beforeChars = 28;
    const int afterChars = 110;
    final int start = (hit.matchStart - beforeChars).clamp(0, full.length);
    final int end = (hit.matchStart + hit.matchLength + afterChars).clamp(0, full.length);

    final String before = full.substring(start, hit.matchStart);
    final String matched = full.substring(hit.matchStart, hit.matchStart + hit.matchLength);
    final String after = full.substring(hit.matchStart + hit.matchLength, end);

    return RichText(
      maxLines: 2,
      overflow: TextOverflow.ellipsis,
      text: TextSpan(
        style: TextStyle(fontSize: 13, color: subTextCol),
        children: [
          if (start > 0) const TextSpan(text: '… '),
          TextSpan(text: before),
          TextSpan(
            text: matched,
            style: TextStyle(fontWeight: FontWeight.bold, color: goldColor),
          ),
          TextSpan(text: after),
          if (end < full.length) const TextSpan(text: ' …'),
        ],
      ),
    );
  }
}
