// screens/search_screen.dart
import 'package:flutter/material.dart';
import '../app_theme.dart';
import '../services/bss_repository.dart';
import '../utils/text_utils.dart';

class SearchResult {
  final int sectionId;
  final int? quoteId;
  final String query;

  const SearchResult({required this.sectionId, this.quoteId, required this.query});
}

class _SearchHit {
  final ContinuousReadingItem item;
  final VerseDetail? verse; // null when only the section title matched
  final int matchStart; // index into the *displayed* text, for highlighting
  final int matchLength;
  final bool matchedInQuote;

  const _SearchHit({
    required this.item,
    required this.verse,
    required this.matchStart,
    required this.matchLength,
    required this.matchedInQuote,
  });
}

/// Simple, fully in-memory, diacritic-insensitive search over everything
/// already loaded for the reading feed. With ~800 quotes total this is
/// instant on every keystroke -- no database changes, no indexing needed.
class SearchScreen extends StatefulWidget {
  final List<ContinuousReadingItem> feedItems;

  const SearchScreen({super.key, required this.feedItems});

  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  final TextEditingController _controller = TextEditingController();
  List<_SearchHit> _results = const [];

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _onQueryChanged(String rawQuery) {
    final String query = normalizeForSearch(rawQuery.trim());
    if (query.isEmpty) {
      setState(() => _results = const []);
      return;
    }

    final List<_SearchHit> quoteMatches = [];
    final List<_SearchHit> titleOnlyMatches = [];

    for (final item in widget.feedItems) {
      bool sectionTitleMatched =
          normalizeForSearch(item.section.title).contains(query);

      bool anyVerseMatched = false;
      for (final verse in item.verses) {
        final String normalizedQuote = normalizeForSearch(verse.quoteText);
        final int idx = normalizedQuote.indexOf(query);
        if (idx != -1) {
          anyVerseMatched = true;
          quoteMatches.add(_SearchHit(
            item: item,
            verse: verse,
            matchStart: idx,
            matchLength: query.length,
            matchedInQuote: true,
          ));
          continue;
        }

        final String normalizedCitation =
            normalizeForSearch('${verse.bookTitle} ${verse.refDisplay}');
        if (normalizedCitation.contains(query)) {
          anyVerseMatched = true;
          quoteMatches.add(_SearchHit(
            item: item,
            verse: verse,
            matchStart: 0,
            matchLength: 0,
            matchedInQuote: false,
          ));
        }
      }

      if (sectionTitleMatched && !anyVerseMatched) {
        titleOnlyMatches.add(_SearchHit(
          item: item,
          verse: null,
          matchStart: 0,
          matchLength: 0,
          matchedInQuote: false,
        ));
      }
    }

    setState(() => _results = [...quoteMatches, ...titleOnlyMatches]);
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
          onChanged: _onQueryChanged,
          style: TextStyle(fontFamily: 'NotoSerif', color: textColor),
          decoration: InputDecoration(
            hintText: 'Search quotes, topics, scriptures…',
            hintStyle: TextStyle(color: subTextCol),
            border: InputBorder.none,
          ),
        ),
        actions: [
          if (_controller.text.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.close),
              onPressed: () {
                _controller.clear();
                _onQueryChanged('');
              },
            ),
        ],
      ),
      body: _buildBody(context, goldColor, textColor, subTextCol),
    );
  }

  Widget _buildBody(BuildContext context, Color goldColor, Color textColor, Color subTextCol) {
    if (_controller.text.trim().isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(
            'Search across all quotes, topic titles, and cited scriptures. '
            'Diacritics are optional -- "krishna" will find "Kṛṣṇa".',
            textAlign: TextAlign.center,
            style: TextStyle(color: subTextCol),
          ),
        ),
      );
    }

    if (_results.isEmpty) {
      return Center(
        child: Text('No matches found.', style: TextStyle(color: subTextCol)),
      );
    }

    return ListView.separated(
      padding: const EdgeInsets.symmetric(vertical: 8),
      itemCount: _results.length,
      separatorBuilder: (_, _) => Divider(height: 1, color: goldColor.withAlpha(60)),
      itemBuilder: (context, index) {
        final hit = _results[index];
        return InkWell(
          onTap: () => Navigator.of(context).pop(
            SearchResult(
              sectionId: hit.item.section.id,
              quoteId: hit.verse?.quoteId,
              query: _controller.text,
            ),
          ),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (hit.verse != null && hit.verse!.bookTitle.isNotEmpty)
                  Text(
                    [hit.verse!.bookTitle, hit.verse!.refDisplay]
                        .where((s) => s.isNotEmpty)
                        .join(' '),
                    style: TextStyle(fontSize: 11, color: goldColor, fontStyle: FontStyle.italic),
                  ),
                if (hit.verse != null && hit.verse!.bookTitle.isNotEmpty)
                  const SizedBox(height: 3),
                Text(
                  hit.item.section.title,
                  style: TextStyle(fontFamily: 'NotoSerif', fontWeight: FontWeight.w600, fontSize: 15, color: textColor),
                ),
                const SizedBox(height: 4),
                _buildSnippet(hit, subTextCol, goldColor),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildSnippet(_SearchHit hit, Color subTextCol, Color goldColor) {
    if (hit.verse == null) {
      return Text(
        '${hit.item.mainPeriod.title} · ${hit.item.subPeriod.timeRange}',
        style: TextStyle(fontSize: 12, color: subTextCol),
      );
    }

    if (!hit.matchedInQuote) {
      // Matched in the citation itself (book name / verse ref), which is
      // already shown as its own line above -- so here just give context
      // by showing the start of the quote, unhighlighted.
      final String preview = hit.verse!.quoteText.length > 120
          ? '${hit.verse!.quoteText.substring(0, 120)}…'
          : hit.verse!.quoteText;
      return Text(
        preview,
        maxLines: 2,
        overflow: TextOverflow.ellipsis,
        style: TextStyle(fontSize: 13, color: subTextCol, fontFamily: 'NotoSerif'),
      );
    }

    final String full = hit.verse!.quoteText;
    // Asymmetric window: short "before" context, generous "after" context.
    // A long "before" window (e.g. matching earlier code's symmetric 70/70)
    // can push the match itself toward the very edge of the 2-line limit,
    // where it either gets clipped by the ellipsis or ends up barely
    // visible on the last visible character. Keeping "before" short means
    // the match reliably lands within the first line or the very start of
    // the second, with plenty of room left to show it's a real match.
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
        style: TextStyle(fontSize: 13, color: subTextCol, fontFamily: 'NotoSerif'),
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
