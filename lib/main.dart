import 'package:flutter/material.dart';

import 'app.dart';
import 'core/database/app_database.dart';
import 'services/csv_import_service.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  await AppDatabase.instance.init();
  await CsvImportService.importAll();

  runApp(
    const BhavanasaraApp(),
  );
}