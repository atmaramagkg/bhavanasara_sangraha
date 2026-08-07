// widgets/app_menu_sheet.dart
import 'package:flutter/material.dart';
import '../app_theme.dart';
import '../services/app_settings.dart';

/// Content of the hamburger menu: language, theme, bookmarks, share.
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
            ListTile(
              leading: Icon(Icons.language, color: goldColor),
              title: Text('Language', style: TextStyle(color: textColor)),
              subtitle: const Text('English'),
              onTap: () {
                Navigator.of(context).pop();
                showDialog(
                  context: context,
                  builder: (_) => const _LanguageDialog(),
                );
              },
            ),
            ListTile(
              leading: Icon(Icons.palette_outlined, color: goldColor),
              title: Text('Theme', style: TextStyle(color: textColor)),
              onTap: () {
                Navigator.of(context).pop();
                showDialog(
                  context: context,
                  builder: (_) => const _ThemeDialog(),
                );
              },
            ),
            ListTile(
              leading: Icon(Icons.text_fields, color: goldColor),
              title: Text('Text Size', style: TextStyle(color: textColor)),
              onTap: () {
                Navigator.of(context).pop();
                showDialog(
                  context: context,
                  builder: (_) => const _FontSizeDialog(),
                );
              },
            ),
            ListTile(
              leading: Icon(Icons.bookmark_outline, color: goldColor),
              title: Text('Bookmarks', style: TextStyle(color: textColor)),
              onTap: () {
                Navigator.of(context).pop();
                onOpenBookmarks();
              },
            ),
            ListTile(
              leading: Icon(Icons.share_outlined, color: goldColor),
              title: Text('Share', style: TextStyle(color: textColor)),
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
    return AlertDialog(
      title: const Text('Language'),
      content: const Text(
        'English is currently the only language available. '
        'More languages may be added in a future update.',
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('OK'),
        ),
      ],
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
          title: const Text('Theme'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              RadioListTile<ThemeMode>(
                title: const Text('Follow system'),
                value: ThemeMode.system,
                groupValue: mode,
                onChanged: (m) => AppSettings.setThemeMode(m!),
              ),
              RadioListTile<ThemeMode>(
                title: const Text('Light (Parchment)'),
                value: ThemeMode.light,
                groupValue: mode,
                onChanged: (m) => AppSettings.setThemeMode(m!),
              ),
              RadioListTile<ThemeMode>(
                title: const Text('Dark (Oak)'),
                value: ThemeMode.dark,
                groupValue: mode,
                onChanged: (m) => AppSettings.setThemeMode(m!),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Done'),
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
        return AlertDialog(
          title: const Text('Text Size'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'Kṛṣṇa left the bower along with the sakhīs.',
                style: TextStyle(fontFamily: 'NotoSerif', fontSize: 15 * scale),
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
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => AppSettings.setFontScale(1.0),
              child: const Text('Reset'),
            ),
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Done'),
            ),
          ],
        );
      },
    );
  }
}
