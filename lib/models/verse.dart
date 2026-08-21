// models/verse.dart
/// A single verse from the unified `verses` table. Contains transliteration,
/// Devanagari Sanskrit text, and translations in all three languages.
class Verse {
  final int id;
  final int? sectionId;
  final int sortOrder;
  final String refDisplay;
  final String transliteration;
  final String translationEn;
  final String translationRu;
  final String translationHi;
  final int? bookId;
  final String sourceRefs;
  final String sanskritText;

  const Verse({
    required this.id,
    this.sectionId,
    this.sortOrder = 0,
    required this.refDisplay,
    this.sourceRefs = '',
    this.transliteration = '',
    this.translationEn = '',
    this.translationRu = '',
    this.translationHi = '',
    this.bookId,
    this.sanskritText = '',
  });

  /// Returns the translation for the given language code.
  /// No cross-language fallback for en/ru (shows nothing if unavailable).
  /// Hindi falls back to English.
  String translationForCode(String code) {
    switch (code) {
      case 'hi':
        if (translationHi.isNotEmpty) return translationHi;
        if (translationEn.isNotEmpty) return translationEn;
        return '';
      case 'ru':
        return translationRu;
      default:
        return translationEn;
    }
  }

  factory Verse.fromMap(Map<String, dynamic> map) {
    return Verse(
      id: (map['id'] as num?)?.toInt() ?? 0,
      sectionId: (map['section_id'] as num?)?.toInt(),
      sortOrder: (map['sort_order'] as num?)?.toInt() ?? 0,
      refDisplay: (map['ref_display'] as String?) ?? '',
      transliteration: (map['transliteration'] as String?) ?? '',
      translationEn: (map['translation_en'] as String?) ?? '',
      translationRu: (map['translation_ru'] as String?) ?? '',
      translationHi: (map['translation_hi'] as String?) ?? '',
      bookId: (map['book_id'] as num?)?.toInt(),
      sourceRefs: (map['source_refs'] as String?) ?? '',
      sanskritText: (map['sanskrit_text'] as String?) ?? '',
    );
  }
}
