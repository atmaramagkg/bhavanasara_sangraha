import 'package:flutter/material.dart';
import 'package:scrollable_positioned_list/scrollable_positioned_list.dart';
import 'package:share_plus/share_plus.dart';
import '../app_theme.dart';
import '../models/lila_period.dart';
import '../services/app_settings.dart';
import '../services/bss_repository.dart';
import '../widgets/app_menu_sheet.dart';
import '../widgets/period_info_sheet.dart';
import 'bookmarks_screen.dart';
import 'books_screen.dart';

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
  // ItemScrollController scrolls to an index directly -- it does not need
  // the target item to already be built, so it works reliably no matter
  // how far away the target is, unlike Scrollable.ensureVisible + GlobalKey.
  final ItemScrollController _itemScrollController = ItemScrollController();
  final ItemPositionsListener _itemPositionsListener =
      ItemPositionsListener.create();

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
    _itemPositionsListener.itemPositions.addListener(_onPositionsChanged);
    _initializeData();
  }

  @override
  void dispose() {
    _itemPositionsListener.itemPositions.removeListener(_onPositionsChanged);
    super.dispose();
  }

  Future<void> _initializeData() async {
    if (!mounted) return;
    setState(() => _isLoading = true);

    try {
      final List<LilaPeriod> mainPeriods = await widget.repository.getMainPeriods();
      final List<ContinuousReadingItem> feedItems = await widget.repository.loadFullContinuousFeed();

      if (!mounted) return;

      _mainPeriods = mainPeriods;
      _feedItems = feedItems;

      int initialIndex = 0;
      if (feedItems.isNotEmpty) {
        initialIndex = feedItems.indexWhere(
          (item) => item.mainPeriod.id == _selectedMainPeriodId,
        );
        if (initialIndex == -1) initialIndex = 0;

        final targetItem = feedItems[initialIndex];
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

      if (feedItems.isNotEmpty) {
        WidgetsBinding.instance.addPostFrameCallback((_) {
          _itemScrollController.jumpTo(index: initialIndex);
        });
      }
    } catch (e) {
      debugPrint('Error initializing data: $e');
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  /// Keeps the top tabs / subperiod bar / right rail in sync with whatever
  /// section the user has scrolled to manually (not via a button tap).
  void _onPositionsChanged() {
    if (_isProgrammaticScroll || _feedItems.isEmpty) return;

    final positions = _itemPositionsListener.itemPositions.value;
    if (positions.isEmpty) return;

    // The topmost item that's still at least partially visible.
    final ItemPosition topMost = positions
        .where((p) => p.itemTrailingEdge > 0)
        .reduce((a, b) => a.itemLeadingEdge < b.itemLeadingEdge ? a : b);

    if (topMost.index < 0 || topMost.index >= _feedItems.length) return;

    final item = _feedItems[topMost.index];
    if (item.section.id == _selectedSectionId) return;

    _updateActiveNavigationSilently(item.mainPeriod.id, item.subPeriod.id, item.section.id);
  }

  Future<void> _updateActiveNavigationSilently(int mainId, int subId, int secId) async {
    List<SubPeriod> subPeriods = _currentSubPeriods;
    final bool mainChanged = mainId != _selectedMainPeriodId;
    if (mainChanged) {
      subPeriods = await widget.repository.getSubPeriods(mainId);
    }
    if (!mounted) return;

    setState(() {
      _selectedMainPeriodId = mainId;
      _selectedSubPeriodId = subId;
      _selectedSectionId = secId;
      if (mainChanged) {
        _currentSubPeriods = subPeriods;
      }
    });
  }

  /// Scrolls the feed so the given section's title lands near the top.
  /// Index-based, so it works whether or not the item has ever been built.
  Future<void> _scrollToSection(int sectionId, {bool animate = true}) async {
    final index = _feedItems.indexWhere((item) => item.section.id == sectionId);
    if (index == -1) {
      debugPrint('Section $sectionId not found in feed');
      return;
    }

    _isProgrammaticScroll = true;

    if (animate) {
      await _itemScrollController.scrollTo(
        index: index,
        duration: const Duration(milliseconds: 400),
        curve: Curves.easeInOut,
        alignment: 0.02,
      );
    } else {
      _itemScrollController.jumpTo(index: index, alignment: 0.02);
    }

    // Small settle delay so the position listener doesn't immediately
    // fight the button-driven selection with its own read of the scroll.
    await Future.delayed(const Duration(milliseconds: 150));
    _isProgrammaticScroll = false;
  }

  Future<void> _onMainPeriodTabSelected(int mainPeriodId) async {
    final subPeriods = await widget.repository.getSubPeriods(mainPeriodId);

    final targetIndex = _feedItems.indexWhere((item) => item.mainPeriod.id == mainPeriodId);
    if (targetIndex == -1) return;
    final targetItem = _feedItems[targetIndex];

    if (!mounted) return;

    setState(() {
      _selectedMainPeriodId = mainPeriodId;
      _currentSubPeriods = subPeriods;
      _selectedSubPeriodId = targetItem.subPeriod.id;
      _selectedSectionId = targetItem.section.id;
    });

    _scrollToSection(targetItem.section.id);
  }

  Future<void> _onSubPeriodSelected(int subPeriodId) async {
    final targetIndex = _feedItems.indexWhere((item) => item.subPeriod.id == subPeriodId);
    if (targetIndex == -1) return;
    final targetItem = _feedItems[targetIndex];

    if (!mounted) return;

    setState(() {
      _selectedSubPeriodId = subPeriodId;
      _selectedMainPeriodId = targetItem.mainPeriod.id;
      _selectedSectionId = targetItem.section.id;
    });

    _scrollToSection(targetItem.section.id);
  }

  void _onSectionRailSelected(int sectionId) {
    setState(() => _selectedSectionId = sectionId);
    _scrollToSection(sectionId);
  }

  void _openPeriodInfoSheet() async {
    final int? liveCurrentId = await widget.repository.getCurrentMainPeriodId();
    if (!mounted) return;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => PeriodInfoSheet(
        periods: _mainPeriods,
        currentPeriodId: liveCurrentId ?? _selectedMainPeriodId,
        onPeriodSelected: _onMainPeriodTabSelected,
      ),
    );
  }

  void _openBooksScreen() {
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => BooksScreen(repository: widget.repository)),
    );
  }

  void _openAppMenu() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => AppMenuSheet(
        onOpenBookmarks: _openBookmarksScreen,
        onShare: _shareCurrentSection,
      ),
    );
  }

  void _openBookmarksScreen() async {
    final int? jumpToSectionId = await Navigator.of(context).push<int>(
      MaterialPageRoute(builder: (_) => BookmarksScreen(repository: widget.repository)),
    );
    if (jumpToSectionId != null) {
      _onSectionRailSelected(jumpToSectionId);
    }
  }

  void _shareCurrentSection() {
    final item = _feedItems.firstWhere(
      (i) => i.section.id == _selectedSectionId,
      orElse: () => _feedItems.first,
    );

    final buffer = StringBuffer()
      ..writeln(item.section.title)
      ..writeln();
    for (final verse in item.verses) {
      buffer.writeln(verse.quoteText);
      if (verse.bookTitle.isNotEmpty || verse.refDisplay.isNotEmpty) {
        buffer.writeln('— ${[verse.bookTitle, verse.refDisplay].where((s) => s.isNotEmpty).join(', ')}');
      }
      buffer.writeln();
    }
    buffer.write('Bhāvanāsāra Saṅgraha');

    SharePlus.instance.share(ShareParams(text: buffer.toString()));
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final goldColor = isDark ? BssColors.darkOakGold : BssColors.goldAccent;
    final cardBg = isDark ? BssColors.darkOakCard : BssColors.parchmentCard;
    final textColor = isDark ? BssColors.darkOakText : BssColors.darkText;
    final subTextCol = isDark ? BssColors.darkOakSubText : BssColors.subText;

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
        leadingWidth: 84,
        leading: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            IconButton(
              icon: const Icon(Icons.access_time),
              tooltip: 'Time periods',
              onPressed: _mainPeriods.isEmpty ? null : _openPeriodInfoSheet,
              color: goldColor,
              disabledColor: goldColor.withAlpha(140),
              iconSize: 20,
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(minWidth: 38, minHeight: 38),
              visualDensity: VisualDensity.compact,
            ),
            IconButton(
              icon: const Icon(Icons.menu_book_outlined),
              tooltip: 'Scriptures quoted',
              onPressed: _openBooksScreen,
              color: goldColor,
              disabledColor: goldColor.withAlpha(140),
              iconSize: 20,
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(minWidth: 38, minHeight: 38),
              visualDensity: VisualDensity.compact,
            ),
          ],
        ),
        title: null,
        actions: [
          ValueListenableBuilder<Set<int>>(
            valueListenable: AppSettings.bookmarkedSectionIds,
            builder: (context, bookmarks, _) {
              final bool isBookmarked = bookmarks.contains(_selectedSectionId);
              return IconButton(
                icon: Icon(isBookmarked ? Icons.bookmark : Icons.bookmark_border),
                tooltip: isBookmarked ? 'Remove bookmark' : 'Bookmark this section',
                onPressed: _selectedSectionId == -1
                    ? null
                    : () => AppSettings.toggleBookmark(_selectedSectionId),
                color: goldColor,
                disabledColor: goldColor.withAlpha(140),
                iconSize: 20,
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(minWidth: 38, minHeight: 38),
                visualDensity: VisualDensity.compact,
              );
            },
          ),
          const SizedBox(width: 2),
          IconButton(
            icon: const Icon(Icons.search),
            tooltip: 'Search (coming soon)',
            onPressed: null,
            color: goldColor,
            disabledColor: goldColor.withAlpha(140),
            iconSize: 20,
            padding: EdgeInsets.zero,
            constraints: const BoxConstraints(minWidth: 38, minHeight: 38),
            visualDensity: VisualDensity.compact,
          ),
          const SizedBox(width: 4),
          IconButton(
            icon: const Icon(Icons.menu),
            tooltip: 'Menu',
            onPressed: _openAppMenu,
            color: goldColor,
            disabledColor: goldColor.withAlpha(140),
            iconSize: 20,
            padding: EdgeInsets.zero,
            constraints: const BoxConstraints(minWidth: 38, minHeight: 38),
            visualDensity: VisualDensity.compact,
          ),
          const SizedBox(width: 8),
        ],
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
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 8.0),
                    child: SizedBox(
                    height: 32,
                    child: Row(
                      children: [
                        for (int index = 0; index < _mainPeriods.length; index++)
                          Expanded(
                            child: Builder(builder: (context) {
                              final period = _mainPeriods[index];
                              final isSelected = (period.id == _selectedMainPeriodId);

                              return Padding(
                                padding: const EdgeInsets.symmetric(horizontal: 2.0),
                                child: GestureDetector(
                                  onTap: () => _onMainPeriodTabSelected(period.id),
                                  child: AnimatedContainer(
                                    duration: const Duration(milliseconds: 180),
                                    decoration: BoxDecoration(
                                      color: isSelected ? goldColor : cardBg,
                                      borderRadius: BorderRadius.circular(6.0),
                                      border: Border.all(color: goldColor, width: 1.0),
                                    ),
                                    child: Center(
                                      child: Text(
                                        '${index + 1}',
                                        style: TextStyle(
                                          fontSize: 13,
                                          fontWeight: FontWeight.bold,
                                          color: isSelected ? (isDark ? BssColors.darkOakBg : Colors.white) : textColor,
                                        ),
                                      ),
                                    ),
                                  ),
                                ),
                              );
                            }),
                          ),
                      ],
                    ),
                  ),
                  ),
                  if (_currentSubPeriods.isNotEmpty) ...[
                    const SizedBox(height: 6),
                    SizedBox(
                      height: 34,
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
                              padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 6.0),
                              margin: const EdgeInsets.symmetric(horizontal: 2.0),
                              decoration: BoxDecoration(
                                color: isSelected ? goldColor.withAlpha(64) : Colors.transparent,
                                borderRadius: BorderRadius.circular(14.0),
                                border: Border.all(color: isSelected ? goldColor : goldColor.withAlpha(76), width: 1.0),
                              ),
                              child: Center(
                                child: Text(
                                  sub.timeRange.isNotEmpty ? sub.timeRange : '${index + 1}',
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
                  ValueListenableBuilder<double>(
                    valueListenable: AppSettings.fontScale,
                    builder: (context, scale, child) {
                      return MediaQuery(
                        data: MediaQuery.of(context).copyWith(
                          textScaler: TextScaler.linear(scale),
                        ),
                        child: child!,
                      );
                    },
                    child: ScrollablePositionedList.builder(
                    itemScrollController: _itemScrollController,
                    itemPositionsListener: _itemPositionsListener,
                    padding: const EdgeInsets.only(left: 12.0, right: 64.0, top: 8.0, bottom: 24.0),
                    itemCount: _feedItems.length,
                    itemBuilder: (context, index) {
                      final item = _feedItems[index];

                      return Padding(
                        padding: const EdgeInsets.symmetric(vertical: 10.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            if (index > 0 && item.isFirstInSubPeriod) ...[
                              Divider(color: goldColor.withAlpha(90), thickness: 1.0),
                              const SizedBox(height: 6),
                            ],
                            if (item.isFirstInMainPeriod) ...[
                              Text(
                                '${item.mainPeriod.id} ${item.mainPeriod.title}',
                                style: TextStyle(fontFamily: 'NotoSerif', fontSize: 16, fontWeight: FontWeight.bold, color: goldColor),
                              ),
                              const SizedBox(height: 4),
                            ],
                            if (item.isFirstInSubPeriod) ...[
                              Text(
                                item.subPeriod.title,
                                style: TextStyle(fontFamily: 'NotoSerif', fontSize: 13, fontWeight: FontWeight.w600, color: textColor),
                              ),
                              const SizedBox(height: 6),
                            ],
                            Text(
                              item.section.title,
                              style: TextStyle(fontFamily: 'NotoSerif', fontSize: 14, fontWeight: FontWeight.bold, color: textColor),
                            ),
                            const SizedBox(height: 8),
                            ...item.verses.map((verse) => Padding(
                              padding: const EdgeInsets.only(bottom: 8.0),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.stretch,
                                children: [
                                  Text(
                                    verse.quoteText,
                                    style: TextStyle(fontFamily: 'NotoSerif', fontSize: 13, color: textColor),
                                  ),
                                  if (verse.bookTitle.isNotEmpty || verse.refDisplay.isNotEmpty) ...[
                                    const SizedBox(height: 3),
                                    Text(
                                      [
                                        if (verse.bookTitle.isNotEmpty) verse.bookTitle,
                                        if (verse.refDisplay.isNotEmpty) verse.refDisplay,
                                      ].join(', '),
                                      textAlign: TextAlign.right,
                                      style: TextStyle(
                                        fontFamily: 'NotoSerif',
                                        fontSize: 11,
                                        fontStyle: FontStyle.italic,
                                        color: subTextCol,
                                      ),
                                    ),
                                  ],
                                ],
                              ),
                            )),
                          ],
                        ),
                      );
                    },
                  ),
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
                                  onTap: () => _onSectionRailSelected(railItem.section.id),
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
