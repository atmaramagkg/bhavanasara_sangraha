/// Language codes that exist as real columns on the `translations` table
/// (see assets/db/Bhavanasara-Sangraha.sqlite: en, ru, hi).
///
/// The selected language code is read back from `app_settings` and then
/// spliced directly into SQL as a column reference (`COALESCE($langCode, ...)`)
/// rather than bound as a `?` parameter, because SQL parameters can only
/// stand in for values, not identifiers. [sanitizeLanguageCode] makes sure
/// only a known-good column name ever reaches that string interpolation.
const Set<String> kValidTranslationLanguageCodes = {'en', 'ru', 'hi'};

String sanitizeLanguageCode(String? code) =>
    kValidTranslationLanguageCodes.contains(code) ? code! : 'en';
