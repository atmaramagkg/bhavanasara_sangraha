import 'package:flutter/material.dart';

import '../core/database/app_database.dart';
import 'period_quotes_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Bhāvanāsāra Saṅgraha'),
      ),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: AppDatabase.instance.getMainPeriods(),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(
              child: CircularProgressIndicator(),
            );
          }

          if (snapshot.hasError) {
            return Center(
              child: Text('Database error: ${snapshot.error}'),
            );
          }

          final periods = snapshot.data ?? [];

          if (periods.isEmpty) {
            return const Center(
              child: Text('No periods found.'),
            );
          }

          return ListView.separated(
            itemCount: periods.length,
            separatorBuilder: (_, __) => const Divider(height: 1),
            itemBuilder: (context, index) {
              final period = periods[index];

              return ListTile(
                leading: CircleAvatar(
                  child: Text("${period['sort_order']}"),
                ),
                title: Text(period['name'] as String),
                subtitle: Text(
                  "${period['time_start']} — ${period['time_end']}",
                ),
                trailing: const Icon(Icons.chevron_right),
                onTap: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => PeriodQuotesScreen(period: period),
                    ),
                  );
                },
              );
            },
          );
        },
      ),
    );
  }
}