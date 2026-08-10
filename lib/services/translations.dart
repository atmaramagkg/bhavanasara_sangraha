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

  /// (Re)loads the map from the currently open database.
  static Future<void> load() async {
    _table = await AppDatabase.instance.loadTranslations();
  }

  /// Switches the app language: opens the matching database file, reloads the
  /// translations and only then notifies the UI via [AppSettings.locale].
  static Future<void> setLanguage(String code) async {
    await AppDatabase.instance.switchDatabase(code);
    await load();
    await AppSettings.setLocale(Locale(code));
  }
}
