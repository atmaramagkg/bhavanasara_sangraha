import 'package:flutter/material.dart';

import 'app.dart';
import 'core/database/app_database.dart';
import 'services/app_settings.dart';
import 'services/csv_import_service.dart';
import 'services/translations.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  await AppSettings.load();
  // Open the database file matching the saved language so the first frame
  // already shows the right language instead of flashing English.
  await AppDatabase.instance.switchDatabase(AppSettings.locale.value.languageCode);
  await CsvImportService.importAll();
  await Translations.load();

  runApp(
    const BhavanasaraApp(),
  );
}