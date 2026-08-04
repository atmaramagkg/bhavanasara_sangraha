import 'package:flutter/material.dart';
import '../core/database/app_database.dart';

class PeriodDetailScreen extends StatelessWidget {
  final Map<String, dynamic> period;

  const PeriodDetailScreen({super.key, required this.period});

  @override
  Widget build(BuildContext context) {
    final int periodId = period['id'] as int;
    final String periodName = period['name'] as String? ?? '';

    return Scaffold(
      appBar: AppBar(title: Text(periodName)),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: AppDatabase.instance.getSubPeriods(periodId),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }

          if (snapshot.hasError) {
            return Center(child: Text('Database error: ${snapshot.error}'));
          }

          final subPeriods = snapshot.data ?? [];

          if (subPeriods.isEmpty) {
            return const Center(
              child: Text('No subperiods yet for this period.'),
            );
          }

          return ListView.separated(
            itemCount: subPeriods.length,
            separatorBuilder: (_, _) => const Divider(height: 1),
            itemBuilder: (context, index) {
              final sub = subPeriods[index];

              return ListTile(
                leading: CircleAvatar(child: Text('${sub['sort_order']}')),
                title: Text(sub['name'] as String? ?? ''),
                trailing: const Icon(Icons.chevron_right),
                onTap: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('Sections screen comes in a next step.'),
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
