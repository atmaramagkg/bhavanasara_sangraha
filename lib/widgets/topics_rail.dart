// widgets/topics_rail.dart
import 'package:flutter/material.dart';
import '../app_theme.dart';
import '../services/bss_repository.dart';

class TopicsRail extends StatelessWidget {
  final List<LilaSectionItem> sections;
  final int selectedSectionId;
  final ValueChanged<int> onSectionSelected;

  const TopicsRail({
    super.key,
    required this.sections,
    required this.selectedSectionId,
    required this.onSectionSelected,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final goldColor = isDark ? BssColors.darkOakGold : BssColors.goldAccent;
    final textColor = isDark ? BssColors.darkOakText : BssColors.darkText;
    final activeCardBg = isDark ? BssColors.darkOakCard : BssColors.parchmentCard;

    if (sections.isEmpty) {
      return const SizedBox(width: 160);
    }

    return Container(
      width: 170,
      decoration: BoxDecoration(
        border: Border(
          right: BorderSide(
            color: goldColor.withValues(alpha: 0.3),
            width: 1.0,
          ),
        ),
      ),
      child: ListView.builder(
        padding: const EdgeInsets.symmetric(vertical: 8.0, horizontal: 6.0),
        itemCount: sections.length,
        itemBuilder: (context, index) {
          final section = sections[index];
          final isSelected = (section.id == selectedSectionId);

          return GestureDetector(
            onTap: () => onSectionSelected(section.id),
            child: Container(
              margin: const EdgeInsets.symmetric(vertical: 3.0),
              padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 8.0),
              decoration: BoxDecoration(
                color: isSelected ? activeCardBg : Colors.transparent,
                borderRadius: BorderRadius.circular(6.0),
                border: Border.all(
                  color: isSelected ? goldColor : Colors.transparent,
                  width: 1.0,
                ),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Numbered Badge
                  Container(
                    width: 18,
                    height: 18,
                    margin: const EdgeInsets.only(top: 2.0, right: 6.0),
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: isSelected ? goldColor : Colors.transparent,
                      border: Border.all(
                        color: goldColor,
                        width: 1.0,
                      ),
                    ),
                    child: Center(
                      child: Text(
                        '${index + 1}',
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          color: isSelected
                              ? (isDark ? BssColors.darkOakBg : Colors.white)
                              : textColor,
                        ),
                      ),
                    ),
                  ),
                  // Topic Title
                  Expanded(
                    child: Text(
                      section.title,
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                        color: textColor,
                        height: 1.2,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}