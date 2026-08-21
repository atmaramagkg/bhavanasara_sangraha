// services/translations.dart
import 'package:flutter/material.dart';

import '../core/database/app_database.dart';
import 'app_settings.dart';

/// Synchronous access to the UI text that lives in the database's
/// `translations` table. The map is (re)loaded whenever the language changes,
/// so widgets can read `Translations.t(key)` without awaiting a query.
class Translations {
  Translations._();

  static Map<String, String> _table = const {};

  /// Returns the translated text for [key], falling back to the key itself
  /// when the database has no entry at all.
  static String t(String key) => _table[key] ?? key;

  /// Returns the translated text for [key] (e.g. 'common.quote') in the
  /// plural form required for [count] in the current UI language, using DB
  /// keys `<key>.one`, `<key>.few`, `<key>.many` and `<key>.other`.
  static String plural(String key, int count) {
    return t('$key.${pluralForm(count)}');
  }

  /// The CLDR-style plural category ('one'/'few'/'many'/'other') that matches
  /// [count] in the current UI language. Falls back to English rules for any
  /// language whose grammar is not implemented here.
  static String pluralForm(int count) {
    final String code = AppSettings.locale.value.languageCode;
    if (code == 'ru') {
      final int mod10 = count % 10;
      final int mod100 = count % 100;
      if (mod10 == 1 && mod100 != 11) return 'one';
      if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) {
        return 'few';
      }
      return 'many';
    }
    if (code == 'hi') {
      return (count == 0 || count == 1) ? 'one' : 'other';
    }
    return count == 1 ? 'one' : 'other';
  }

  /// Translates a normalized source_ref like 'govinda-lilamrta 1.107-108'
  /// into the currently active UI language.
  static String translateSourceRef(String ref) {
    if (ref.isEmpty) return '';
    final idx = ref.indexOf(' ');
    if (idx < 0) return t('book.$ref.title');
    final slug = ref.substring(0, idx);
    final verseRef = ref.substring(idx + 1);
    final bookName = t('book.$slug.title');
    return '$bookName $verseRef';
  }

  /// (Re)loads the map from the currently open database.
  static Future<void> load() async {
    _table = await AppDatabase.instance.loadTranslations();
  }

  /// Switches the app language: persists the code, reloads translations and
  /// updates the locale via AppSettings. No longer needs to swap database files
  /// because all languages live in the single unified database.
  static Future<void> setLanguage(String code) async {
    await AppDatabase.instance.setCurrentLanguageCode(code);
    await load();
    await AppSettings.setLocale(Locale(code));
  }
}
