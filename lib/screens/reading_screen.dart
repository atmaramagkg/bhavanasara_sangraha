import 'package:flutter/material.dart';
import '../app_theme.dart';
import '../models/lila_period.dart';
import '../services/bss_repository.dart';

class ReadingScreen extends StatefulWidget {
  final BssRepository repository;
  final int initialPeriodId;

  const ReadingScreen({
    super.key,
    required this.repository,
    this.initialPeriodId = 1,
  });

  @override
  State<ReadingScreen> createState() => _ReadingScreenState();
}

class _ReadingScreenState extends State<ReadingScreen> {
  final ScrollController _scrollController = ScrollController();
  final Map<int, GlobalKey> _sectionKeys = {};

  List<LilaPeriod> _mainPeriods = [];
  List<SubPeriod> _currentSubPeriods = [];
  List<ContinuousReadingItem> _feedItems = [];

  int _selectedMainPeriodId = 1;
  int _selectedSubPeriodId = -1;
  int _selectedSectionId = -1;
  bool _isLoading = true;
  bool _isProgrammaticScroll = false;

  @override
  void initState() {
    super.initState();
    _selectedMainPeriodId = widget.initialPeriodId;
    _scrollController.addListener(_onScroll);
    _initializeData();
  }

  @override
  void dispose() {
    _scrollController.removeListener(_onScroll);
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _initializeData() async {
    if (!mounted) return;
    setState(() => _isLoading = true);

    final List<LilaPeriod> mainPeriods = await widget.repository.getMainPeriods();
    final List<ContinuousReadingItem> feedItems = await widget.repository.loadFullContinuousFeed();

    if (!mounted) return;

    _sectionKeys.clear();
    for (final item in feedItems) {
      _sectionKeys[item.section.id] = GlobalKey();
    }

    _mainPeriods = mainPeriods;
    _feedItems = feedItems;

    if (feedItems.isNotEmpty) {
      final targetItem = feedItems.firstWhere(
        (item) => item.mainPeriod.id == _selectedMainPeriodId,
        orElse: () => feedItems.first,
      );

      _selectedMainPeriodId = targetItem.mainPeriod.id;
      _selectedSubPeriodId = targetItem.subPeriod.id;
      _selectedSectionId = targetItem.section.id;
    }

    final subPeriods = await widget.repository.getSubPeriods(_selectedMainPeriodId);
    if (!mounted) return;

    setState(() {
      _currentSubPeriods = subPeriods;
      if (!subPeriods.any((s) => s.id == _selectedSubPeriodId) && subPeriods.isNotEmpty) {
        _selectedSubPeriodId = subPeriods.first.id;
      }
      _isLoading = false;
    });

    if (_selectedSectionId != -1) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _scrollToSection(_selectedSectionId, animate: false);
      });
    }
  }

  void _onScroll() {
    if (_isProgrammaticScroll || _feedItems.isEmpty || !_scrollController.hasClients) return;

    for (final item in _feedItems) {
      final key = _sectionKeys[item.section.id];
      if (key?.currentContext != null) {
        final renderBox = key!.currentContext!.findRenderObject() as RenderBox?;
        if (renderBox != null) {
          final position = renderBox.localToGlobal(Offset.zero);
          if (position.dy >= -20 && position.dy <= 300) {
            if (_selectedSectionId != item.section.id ||
                _selectedSubPeriodId != item.subPeriod.id ||
                _selectedMainPeriodId != item.mainPeriod.id) {
              _updateActiveNavigationSilently(item.mainPeriod.id, item.subPeriod.id, item.section.id);
            }
            break;
          }
        }
      }
    }
  }

  Future<void> _updateActiveNavigationSilently(int mainId, int subId, int secId) async {
    List<SubPeriod> subPeriods = _currentSubPeriods;
    if (mainId != _selectedMainPeriodId) {
      subPeriods = await widget.repository.getSubPeriods(mainId);
    }
    if (!mounted) return;

    setState(() {
      _selectedMainPeriodId = mainId;
      _selectedSubPeriodId = subId;
      _selectedSectionId = secId;
      if (mainId != _selectedMainPeriodId) {
        _currentSubPeriods = subPeriods;
      }
    });
  }

  void _scrollToSection(int sectionId, {bool animate = true}) {
    final key = _sectionKeys[sectionId];
    _isProgrammaticScroll = true;

    final targetItem = _feedItems.firstWhere(
      (item) => item.section.id == sectionId,
      orElse: () => _feedItems.first,
    );

    setState(() {
      _selectedSectionId = sectionId;
      _selectedMainPeriodId = targetItem.mainPeriod.id;
      _selectedSubPeriodId = targetItem.subPeriod.id;
    });

    if (key != null && key.currentContext != null) {
      Scrollable.ensureVisible(
        key.currentContext!,
        duration: Duration(milliseconds: animate ? 350 : 0),
        curve: Curves.easeInOut,
        alignment: 0.0,
      ).then((_) {
        Future.delayed(const Duration(milliseconds: 200), () {
          _isProgrammaticScroll = false;
        });
      });
    } else {
      final index = _feedItems.indexWhere((item) => item.section.id == sectionId);
      if (index != -1 && _scrollController.hasClients) {
        final estimatedOffset = index * 180.0;
        _scrollController.animateTo(
          estimatedOffset.clamp(0.0, _scrollController.position.maxScrollExtent),
          duration: Duration(milliseconds: animate ? 350 : 0),
          curve: Curves.easeInOut,
        ).then((_) {
          Future.delayed(const Duration(milliseconds: 200), () {
            _isProgrammaticScroll = false;
          });
        });
      } else {
        _isProgrammaticScroll = false;
      }
    }
  }

  Future<void> _onMainPeriodTabSelected(int mainPeriodId) async {
    final subPeriods = await widget.repository.getSubPeriods(mainPeriodId);
    
    final targetItem = _feedItems.firstWhere(
      (item) => item.mainPeriod.id == mainPeriodId,
      orElse: () => _feedItems.first,
    );

    if (!mounted) return;

    setState(() {
      _selectedMainPeriodId = mainPeriodId;
      _currentSubPeriods = subPeriods;
      if (subPeriods.isNotEmpty) {
        _selectedSubPeriodId = subPeriods.first.id;
      }
      _selectedSectionId = targetItem.section.id;
    });

    _scrollToSection(targetItem.section.id);
  }

  Future<void> _onSubPeriodSelected(int subPeriodId) async {
    final targetItem = _feedItems.firstWhere(
      (item) => item.subPeriod.id == subPeriodId,
      orElse: () => _feedItems.first,
    );

    if (!mounted) return;

    setState(() {
      _selectedSubPeriodId = subPeriodId;
      _selectedMainPeriodId = targetItem.mainPeriod.id;
      _selectedSectionId = targetItem.section.id;
    });

    _scrollToSection(targetItem.section.id);
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final goldColor = isDark ? BssColors.darkOakGold : BssColors.goldAccent;
    final cardBg = isDark ? BssColors.darkOakCard : BssColors.parchmentCard;
    final textColor = isDark ? BssColors.darkOakText : BssColors.darkText;

    if (_isLoading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    final activeRailItems = _feedItems
        .where((item) => item.subPeriod.id == _selectedSubPeriodId)
        .toList();

    return Scaffold(
      appBar: AppBar(
        automaticallyImplyLeading: false,
        title: const Text(
          'Bhāvanāsāra Saṅgraha',
          style: TextStyle(fontFamily: 'Serif', fontSize: 16),
        ),
        centerTitle: true,
      ),
      body: SafeArea(
        child: Column(
          children: [
            Container(
              padding: const EdgeInsets.symmetric(vertical: 6.0),
              decoration: BoxDecoration(
                color: isDark ? BssColors.darkOakBg : BssColors.parchmentBg,
                border: Border(bottom: BorderSide(color: goldColor.withAlpha(76), width: 1.0)),
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  SizedBox(
                    height: 36,
                    child: ListView.builder(
                      scrollDirection: Axis.horizontal,
                      itemCount: _mainPeriods.length,
                      padding: const EdgeInsets.symmetric(horizontal: 8.0),
                      itemBuilder: (context, index) {
                        final period = _mainPeriods[index];
                        final isSelected = (period.id == _selectedMainPeriodId);

                        return GestureDetector(
                          onTap: () => _onMainPeriodTabSelected(period.id),
                          child: AnimatedContainer(
                            duration: const Duration(milliseconds: 180),
                            padding: const EdgeInsets.symmetric(horizontal: 10.0, vertical: 4.0),
                            margin: const EdgeInsets.symmetric(horizontal: 2.0),
                            decoration: BoxDecoration(
                              color: isSelected ? goldColor : cardBg,
                              borderRadius: BorderRadius.circular(6.0),
                              border: Border.all(color: goldColor, width: 1.0),
                            ),
                            child: Center(
                              child: Text(
                                '${index + 1} ${period.title}',
                                style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.bold,
                                  color: isSelected ? (isDark ? BssColors.darkOakBg : Colors.white) : textColor,
                                ),
                              ),
                            ),
                          ),
                        );
                      },
                    ),
                  ),
                  if (_currentSubPeriods.isNotEmpty) ...[
                    const SizedBox(height: 6),
                    SizedBox(
                      height: 28,
                      child: ListView.builder(
                        scrollDirection: Axis.horizontal,
                        itemCount: _currentSubPeriods.length,
                        padding: const EdgeInsets.symmetric(horizontal: 8.0),
                        itemBuilder: (context, index) {
                          final sub = _currentSubPeriods[index];
                          final isSelected = (sub.id == _selectedSubPeriodId);

                          return GestureDetector(
                            onTap: () => _onSubPeriodSelected(sub.id),
                            child: AnimatedContainer(
                              duration: const Duration(milliseconds: 180),
                              padding: const EdgeInsets.symmetric(horizontal: 10.0, vertical: 4.0),
                              margin: const EdgeInsets.symmetric(horizontal: 3.0),
                              decoration: BoxDecoration(
                                color: isSelected ? goldColor.withAlpha(64) : Colors.transparent,
                                borderRadius: BorderRadius.circular(14.0),
                                border: Border.all(color: isSelected ? goldColor : goldColor.withAlpha(76), width: 1.0),
                              ),
                              child: Center(
                                child: Text(
                                  '${index + 1} ${sub.title}',
                                  style: TextStyle(
                                    fontSize: 10,
                                    fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                                    color: isSelected ? goldColor : textColor,
                                  ),
                                ),
                              ),
                            ),
                          );
                        },
                      ),
                    ),
                  ],
                ],
              ),
            ),
            Expanded(
              child: Stack(
                children: [
                  ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.only(left: 12.0, right: 64.0, top: 8.0, bottom: 24.0),
                    itemCount: _feedItems.length,
                    itemBuilder: (context, index) {
                      final item = _feedItems[index];
                      final key = _sectionKeys[item.section.id];

                      return Container(
                        key: key,
                        margin: const EdgeInsets.only(bottom: 12.0),
                        padding: const EdgeInsets.all(14.0),
                        decoration: BoxDecoration(
                          color: cardBg,
                          borderRadius: BorderRadius.circular(8.0),
                          border: Border.all(color: goldColor.withAlpha(102), width: 1.0),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            if (item.isFirstInMainPeriod) ...[
                              Text(
                                '${item.mainPeriod.id} ${item.mainPeriod.title}',
                                style: TextStyle(fontFamily: 'Serif', fontSize: 16, fontWeight: FontWeight.bold, color: goldColor),
                              ),
                              const SizedBox(height: 4),
                            ],
                            if (item.isFirstInSubPeriod) ...[
                              Text(
                                '${item.subPeriod.title}',
                                style: TextStyle(fontFamily: 'Serif', fontSize: 13, fontWeight: FontWeight.w600, color: textColor),
                              ),
                              const SizedBox(height: 6),
                            ],
                            Text(
                              item.section.title,
                              style: TextStyle(fontFamily: 'Serif', fontSize: 14, fontWeight: FontWeight.bold, color: textColor),
                            ),
                            const SizedBox(height: 8),
                            ...item.verses.map((verse) => Padding(
                              padding: const EdgeInsets.only(bottom: 6.0),
                              child: Text(
                                verse.quoteText,
                                style: TextStyle(fontFamily: 'Serif', fontSize: 13, color: textColor),
                              ),
                            )),
                          ],
                        ),
                      );
                    },
                  ),
                  Positioned(
                    right: 0,
                    top: 0,
                    bottom: 0,
                    child: Container(
                      width: 52,
                      padding: const EdgeInsets.symmetric(vertical: 6.0, horizontal: 2.0),
                      decoration: BoxDecoration(
                        color: (isDark ? BssColors.darkOakCard : BssColors.parchmentCard).withAlpha(240),
                        border: Border(left: BorderSide(color: goldColor.withAlpha(102), width: 1.0)),
                      ),
                      child: Column(
                        children: [
                          Text('${activeRailItems.length}', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: goldColor)),
                          const Divider(height: 8),
                          Expanded(
                            child: ListView.builder(
                              itemCount: activeRailItems.length,
                              padding: EdgeInsets.zero,
                              itemBuilder: (context, idx) {
                                final railItem = activeRailItems[idx];
                                final isSelected = (railItem.section.id == _selectedSectionId);

                                return GestureDetector(
                                  onTap: () => _scrollToSection(railItem.section.id),
                                  child: Container(
                                    margin: const EdgeInsets.symmetric(vertical: 4.0),
                                    alignment: Alignment.center,
                                    child: AnimatedContainer(
                                      duration: const Duration(milliseconds: 180),
                                      width: 28,
                                      height: 28,
                                      decoration: BoxDecoration(
                                        shape: BoxShape.circle,
                                        color: isSelected ? goldColor : Colors.transparent,
                                        border: Border.all(color: goldColor, width: 1.2),
                                      ),
                                      child: Center(
                                        child: Text(
                                          '${idx + 1}',
                                          style: TextStyle(
                                            fontSize: 11,
                                            fontWeight: FontWeight.bold,
                                            color: isSelected ? (isDark ? BssColors.darkOakBg : Colors.white) : textColor,
                                          ),
                                        ),
                                      ),
                                    ),
                                  ),
                                );
                              },
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}