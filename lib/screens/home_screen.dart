import 'package:flutter/material.dart';
import '../core/database/app_database.dart';
import '../services/bss_repository.dart';
import 'reading_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return FutureBuilder(
      future: AppDatabase.instance.database,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }

        if (snapshot.hasError) {
          return Scaffold(
            body: Center(child: Text('Database Error: ${snapshot.error}')),
          );
        }

        final db = snapshot.data;
        if (db == null) {
          return const Scaffold(
            body: Center(child: Text('Failed to load database instance.')),
          );
        }

        final repository = BssRepository(db);

        // Open on whichever period (main + sub) the clock says it is right
        // now, falling back to period 1 if that lookup ever fails.
        return FutureBuilder<({int mainPeriodId, int subPeriodId})?>(
          future: repository.getCurrentPeriodPair(),
          builder: (context, periodSnapshot) {
            if (periodSnapshot.connectionState == ConnectionState.waiting) {
              return const Scaffold(
                body: Center(child: CircularProgressIndicator()),
              );
            }

            final current = periodSnapshot.data;
            return ReadingScreen(
              repository: repository,
              initialPeriodId: current?.mainPeriodId ?? 1,
              initialSubPeriodId: current?.subPeriodId,
            );
          },
        );
      },
    );
  }
}
