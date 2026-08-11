// models/verse.dart
/// A single verse (or verse range) of a source scripture, as stored in the
/// `verses` table. Full texts are being added gradually, so any of the text
/// fields may still be empty for verses that only exist as quotes so far.
class Verse {
  final int id;
  final int bookId;
  final String? division1;
  final String? division2;
  final String? chapter;
  final String? section;
  final String? verseStart;
  final String? verseEnd;
  final String refDisplay;
  final String originalText;
  final String originalTextDevanagari;
  final String translationText;
  final String commentaryText;
  final int sortOrder;

  const Verse({
    required this.id,
    required this.bookId,
    this.division1,
    this.division2,
    this.chapter,
    this.section,
    this.verseStart,
    this.verseEnd,
    required this.refDisplay,
    required this.originalText,
    this.originalTextDevanagari = '',
    required this.translationText,
    required this.commentaryText,
    this.sortOrder = 0,
  });

  factory Verse.fromMap(Map<String, dynamic> map) {
    return Verse(
      id: (map['id'] as num?)?.toInt() ?? 0,
      bookId: (map['book_id'] as num?)?.toInt() ?? 0,
      division1: map['division_1'] as String?,
      division2: map['division_2'] as String?,
      chapter: map['chapter'] as String?,
      section: map['section'] as String?,
      verseStart: map['verse_start'] as String?,
      verseEnd: map['verse_end'] as String?,
      refDisplay: (map['ref_display'] as String?) ?? '',
      originalText: (map['original_text'] as String?) ?? '',
      originalTextDevanagari:
          (map['original_text_devanagari'] as String?) ?? '',
      translationText: (map['translation_text'] as String?) ?? '',
      commentaryText: (map['commentary_text'] as String?) ?? '',
      sortOrder: (map['sort_order'] as num?)?.toInt() ?? 0,
    );
  }
}
