// widgets/verse_reader_card.dart
import 'package:flutter/material.dart';
import '../app_theme.dart';
import '../services/bss_repository.dart';

enum ScriptMode { sanskrit, transliteration, translation, all }

class VerseReaderCard extends StatefulWidget {
  final List<VerseDetail> verses;
  final String sectionTitle;

  const VerseReaderCard({
    super.key,
    required this.verses,
    required this.sectionTitle,
  });

  @override
  State<VerseReaderCard> createState() => _VerseReaderCardState();
}

class _VerseReaderCardState extends State<VerseReaderCard> {
  ScriptMode _selectedMode = ScriptMode.all;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final goldColor = isDark ? BssColors.darkOakGold : BssColors.goldAccent;
    final cardBg = isDark ? BssColors.darkOakCard : BssColors.parchmentCard;
    final textColor = isDark ? BssColors.darkOakText : BssColors.darkText;
    final subTextColor = isDark ? BssColors.darkOakSubText : BssColors.subText;

    if (widget.verses.isEmpty) {
      return Center(
        child: Text(
          '...',
          style: TextStyle(color: subTextColor),
        ),
      );
    }

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 8.0),
      padding: const EdgeInsets.all(12.0),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(12.0),
        border: Border.all(
          color: goldColor.withValues(alpha: 0.4),
          width: 1.0,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Section Title
          Text(
            widget.sectionTitle,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontFamily: 'NotoSerif',
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: textColor,
            ),
          ),
          const SizedBox(height: 8),

          // Horizontal scrollable script mode selector (Prevents overflow)
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: SegmentedButton<ScriptMode>(
              showSelectedIcon: false,
              segments: const [
                ButtonSegment(value: ScriptMode.all, label: Text('All', style: TextStyle(fontSize: 10))),
                ButtonSegment(value: ScriptMode.sanskrit, label: Text('Sanskrit', style: TextStyle(fontSize: 10))),
                ButtonSegment(value: ScriptMode.transliteration, label: Text('IAST', style: TextStyle(fontSize: 10))),
                ButtonSegment(value: ScriptMode.translation, label: Text('Translation', style: TextStyle(fontSize: 10))),
              ],
              selected: {_selectedMode},
              onSelectionChanged: (Set<ScriptMode> newSelection) {
                setState(() {
                  _selectedMode = newSelection.first;
                });
              },
              style: ButtonStyle(
                visualDensity: VisualDensity.compact,
                padding: WidgetStateProperty.all(const EdgeInsets.symmetric(horizontal: 8)),
                side: WidgetStateProperty.all(BorderSide(color: goldColor.withValues(alpha: 0.5))),
              ),
            ),
          ),
          const SizedBox(height: 8),
          const Divider(height: 1),
          const SizedBox(height: 8),

          // Reading Text Area
          Expanded(
            child: ListView.separated(
              itemCount: widget.verses.length,
              separatorBuilder: (context, index) => Padding(
                padding: const EdgeInsets.symmetric(vertical: 8.0),
                child: Center(
                  child: Icon(
                    Icons.star_border_rounded,
                    size: 14,
                    color: goldColor.withValues(alpha: 0.6),
                  ),
                ),
              ),
              itemBuilder: (context, index) {
                final verse = widget.verses[index];

                return Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    SelectableText(
                      verse.quoteText,
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontFamily: 'NotoSerif',
                        fontSize: 15,
                        height: 1.5,
                        color: textColor,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      // refDisplay already includes the book name + verse
                      // ref -- pairing it with bookTitle used to duplicate
                      // the book name.
                      '— ${verse.refDisplay.isNotEmpty ? verse.refDisplay : verse.bookTitle}',
                      textAlign: TextAlign.right,
                      style: TextStyle(
                        fontFamily: 'NotoSerif',
                        fontSize: 11,
                        fontStyle: FontStyle.italic,
                        color: goldColor,
                      ),
                    ),
                  ],
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}