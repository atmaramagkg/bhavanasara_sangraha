// widgets/app_menu_sheet.dart
import 'package:flutter/material.dart';
import '../app_theme.dart';
import '../core/database/app_database.dart';
import '../services/app_settings.dart';
import '../services/translations.dart';

/// Content of the hamburger menu: language, theme, bookmarks, share.
/// All labels come from the `translations` table of the active database.
class AppMenuSheet extends StatelessWidget {
  final VoidCallback onOpenBookmarks;
  final VoidCallback onShare;

  const AppMenuSheet({
    super.key,
    required this.onOpenBookmarks,
    required this.onShare,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final goldColor = isDark ? BssColors.darkOakGold : BssColors.goldAccent;
    final textColor = isDark ? BssColors.darkOakText : BssColors.darkText;

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 36,
              height: 4,
              margin: const EdgeInsets.only(bottom: 8),
              decoration: BoxDecoration(
                color: goldColor.withAlpha(140),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            ValueListenableBuilder<Locale>(
              valueListenable: AppSettings.locale,
              builder: (context, locale, _) {
                return ListTile(
                  leading: Icon(Icons.language, color: goldColor),
                  title: Text(
                    Translations.t('menu.language'),
                    style: TextStyle(color: textColor),
                  ),
                  subtitle: Text(
                    switch (locale.languageCode) {
                      'ru' => Translations.t('language.russian'),
                      'hi' => Translations.t('language.hindi'),
                      _ => Translations.t('language.english'),
                    },
                    style: TextStyle(color: textColor.withAlpha(180)),
                  ),
                  onTap: () {
                    showDialog(
                      context: context,
                      builder: (_) => const _LanguageDialog(),
                    );
                  },
                );
              },
            ),
            ListTile(
              leading: Icon(Icons.palette_outlined, color: goldColor),
              title: Text(
                Translations.t('menu.theme'),
                style: TextStyle(color: textColor),
              ),
              onTap: () {
                showDialog(
                  context: context,
                  builder: (_) => const _ThemeDialog(),
                );
              },
            ),
            ListTile(
              leading: Icon(Icons.text_fields, color: goldColor),
              title: Text(
                Translations.t('menu.textSize'),
                style: TextStyle(color: textColor),
              ),
              onTap: () {
                showDialog(
                  context: context,
                  builder: (_) => const _FontSizeDialog(),
                );
              },
            ),
            ListTile(
              leading: Icon(Icons.bookmark_outline, color: goldColor),
              title: Text(
                Translations.t('menu.bookmarks'),
                style: TextStyle(color: textColor),
              ),
              onTap: () {
                Navigator.of(context).pop();
                onOpenBookmarks();
              },
            ),
            ListTile(
              leading: Icon(Icons.share_outlined, color: goldColor),
              title: Text(
                Translations.t('menu.share'),
                style: TextStyle(color: textColor),
              ),
              onTap: () {
                Navigator.of(context).pop();
                onShare();
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _LanguageDialog extends StatelessWidget {
  const _LanguageDialog();

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<Locale>(
      valueListenable: AppSettings.locale,
      builder: (context, locale, _) {
        return AlertDialog(
          title: Text(Translations.t('menu.language')),
          content: FutureBuilder<List<AvailableLanguage>>(
            future: AppDatabase.availableLanguages(),
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) {
                return const SizedBox(
                  height: 120,
                  child: Center(child: CircularProgressIndicator()),
                );
              }
              final languages =
                  snapshot.data ?? const <AvailableLanguage>[];
              return RadioGroup<Locale>(
                groupValue: locale,
                onChanged: (Locale? value) {
                  if (value != null) {
                    Translations.setLanguage(value.languageCode);
                  }
                },
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    for (final AvailableLanguage language in languages)
                      RadioListTile<Locale>(
                        title: Text(language.name),
                        value: Locale(language.code),
                      ),
                  ],
                ),
              );
            },
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: Text(Translations.t('common.done')),
            ),
          ],
        );
      },
    );
  }
}

class _ThemeDialog extends StatelessWidget {
  const _ThemeDialog();

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<ThemeMode>(
      valueListenable: AppSettings.themeMode,
      builder: (context, mode, _) {
        return AlertDialog(
          title: Text(Translations.t('menu.theme')),
          content: RadioGroup<ThemeMode>(
            groupValue: mode,
            onChanged: (m) => AppSettings.setThemeMode(m!),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                RadioListTile<ThemeMode>(
                  title: Text(Translations.t('theme.followSystem')),
                  value: ThemeMode.system,
                ),
                RadioListTile<ThemeMode>(
                  title: Text(Translations.t('theme.lightParchment')),
                  value: ThemeMode.light,
                ),
                RadioListTile<ThemeMode>(
                  title: Text(Translations.t('theme.darkOak')),
                  value: ThemeMode.dark,
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: Text(Translations.t('common.done')),
            ),
          ],
        );
      },
    );
  }
}

class _FontSizeDialog extends StatelessWidget {
  const _FontSizeDialog();

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<double>(
      valueListenable: AppSettings.fontScale,
      builder: (context, scale, _) {
        return ValueListenableBuilder<String>(
          valueListenable: AppSettings.fontFamily,
          builder: (context, fontFamily, _) {
            return AlertDialog(
              title: Text(Translations.t('menu.textSize')),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    Translations.t('sample.readingText'),
                    style: TextStyle(
                      fontFamily: fontFamily,
                      fontSize: 15 * scale,
                    ),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      const Icon(Icons.text_decrease, size: 18),
                      Expanded(
                        child: Slider(
                          value: scale,
                          min: AppSettings.minFontScale,
                          max: AppSettings.maxFontScale,
                          divisions: 15,
                          label: '${(scale * 100).round()}%',
                          onChanged: (v) => AppSettings.setFontScale(v),
                        ),
                      ),
                      const Icon(Icons.text_increase, size: 22),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Align(
                    alignment: Alignment.centerLeft,
                    child: Text(
                      Translations.t('menu.fontFamily'),
                      style: const TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  RadioGroup<String>(
                    groupValue: fontFamily,
                    onChanged: (String? value) {
                      if (value != null) AppSettings.setFontFamily(value);
                    },
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        RadioListTile<String>(
                          dense: true,
                          title: Text(
                            Translations.t('font.serif'),
                            style: TextStyle(fontFamily: AppSettings.fontSerif),
                          ),
                          value: AppSettings.fontSerif,
                        ),
                        RadioListTile<String>(
                          dense: true,
                          title: Text(
                            Translations.t('font.sans'),
                            style: TextStyle(fontFamily: AppSettings.fontSans),
                          ),
                          value: AppSettings.fontSans,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              actions: [
                TextButton(
                  onPressed: () => AppSettings.setFontScale(1.0),
                  child: Text(Translations.t('common.reset')),
                ),
                TextButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: Text(Translations.t('common.done')),
                ),
              ],
            );
          },
        );
      },
    );
  }
}
