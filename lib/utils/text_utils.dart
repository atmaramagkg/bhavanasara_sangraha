// utils/text_utils.dart

/// Strips common IAST Sanskrit diacritics down to plain ASCII and
/// lowercases, so a search for "krishna" (typed on an ordinary keyboard)
/// still matches "Kṛṣṇa" in the text.
///
/// This is always a 1:1 character substitution -- it never changes the
/// string's length -- so an index found in the normalized string points
/// at the exact same position in the original string. That's what lets
/// search results show a snippet with correct diacritics and casing
/// straight from the original text, instead of the flattened search copy.
String normalizeForSearch(String input) {
  final buffer = StringBuffer();
  for (final int rune in input.runes) {
    final String ch = String.fromCharCode(rune);
    buffer.write(_diacriticMap[ch] ?? ch);
  }
  return buffer.toString().toLowerCase();
}

const Map<String, String> _diacriticMap = {
  'ā': 'a', 'Ā': 'A',
  'ī': 'i', 'Ī': 'I',
  'ū': 'u', 'Ū': 'U',
  'ṛ': 'r', 'Ṛ': 'R',
  'ṝ': 'r', 'Ṝ': 'R',
  'ḷ': 'l', 'Ḷ': 'L',
  'ḹ': 'l', 'Ḹ': 'L',
  'ṃ': 'm', 'Ṃ': 'M',
  'ṁ': 'm', 'Ṁ': 'M',
  'ḥ': 'h', 'Ḥ': 'H',
  'ś': 's', 'Ś': 'S',
  'ṣ': 's', 'Ṣ': 'S',
  'ñ': 'n', 'Ñ': 'N',
  'ṅ': 'n', 'Ṅ': 'N',
  'ṭ': 't', 'Ṭ': 'T',
  'ḍ': 'd', 'Ḍ': 'D',
  'ṇ': 'n', 'Ṇ': 'N',
  '’': "'", '‘': "'",
  '“': '"', '”': '"',
  '—': '-', '–': '-',
};
