// views/home_view.dart

import 'dart:async';
import 'package:flutter/material.dart';
import 'package:dphoc/services/google_sheets_service.dart'; // Import GoogleSheetsService
import 'package:dphoc/services/connectivity_service.dart';
import 'package:dphoc/views/school_contacts_view.dart';
import 'package:dphoc/views/inspector_overview_view.dart';
import 'package:dphoc/views/direction_overview_view.dart';  // Import the Direction Overview view

class HomeView extends StatefulWidget {
  const HomeView({super.key});

  @override
  State<HomeView> createState() => _HomeViewState();
}

class _HomeViewState extends State<HomeView> {
  late GoogleSheetsService _sheetsService;
  late ConnectivityService _connectivityService;
  bool _isLoading = false;
  String? _message;
  Color? _messageColor;

  @override
  void initState() {
    super.initState();
    _sheetsService = GoogleSheetsService(); // Initialisation correcte
    _connectivityService = ConnectivityService();
    _loadAppState();
  }

  @override
  void dispose() {
    _connectivityService.dispose();
    super.dispose();
  }

  Future<void> _loadAppState() async {
    String route = await _sheetsService.loadState();
  }

  Future<void> _updateData() async {
    setState(() {
      _isLoading = true;
      _message = null;
    });

    bool isConnected = await _sheetsService.isConnectedToInternet();

    if (isConnected) {
      try {
        _sheetsService.clearCache();
        await _sheetsService.downloadAllSheets(); // Download all sheets
        
        setState(() {
          _message = "تم تحديث البيانات بنجاح.";
          _messageColor = Colors.green;
        });
      } catch (e) {
        setState(() {
          _message = "حدث خطأ أثناء التحديث: $e";
          _messageColor = Colors.red;
        });
      }
    } else {
      setState(() {
        _message = "لا يوجد اتصال بالإنترنت.";
        _messageColor = Colors.red;
      });
    }

    _showMessageAfterProgress();
  }

  void _showMessageAfterProgress() {
    Future.delayed(const Duration(seconds: 2), () {
      if (mounted) {
        setState(() {
          _isLoading = false; // Hide the progress bar
        });
      }

      Future.delayed(const Duration(seconds: 2), () {
        if (mounted) {
          setState(() {
            _message = null; // Clear the message
          });
        }
      });
    });
  }
  @override
  Widget build(BuildContext context) {
    final screenWidth = MediaQuery.of(context).size.width;
    final double buttonWidth = screenWidth > 500 ? 380.0 : 320.0; // Increased button width
    final double buttonHeight = screenWidth > 500 ? 70.0 : 60.0; // Increased button height
    final textSize = screenWidth > 500 ? 26.0 : 22.0; // Adjusted for better appearance with custom font

    final buttonColors = {
      'مصالح المديرية': Colors.blue,
      'أطر التفتيش والتوجيه': Colors.deepPurple,  // Button for inspector overview
      'التعليم الإبتدائي': Colors.green,
      'الثانوي الإعدادي': Colors.orange,
      'الثانوي التأهيلي': Colors.cyan,
    };

    return Scaffold(
      body: Stack(
        children: [
          // Gradient background that fills the entire screen
          Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: [Color(0xFFe0f7fa), Color(0xFF80deea)], // Ice style gradient colors
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
              ),
            ),
          ),
          // Content
          SingleChildScrollView(
            child: SafeArea(
              child: Container(
                // To ensure the Container fills the height of the screen
                constraints: BoxConstraints(
                  minHeight: MediaQuery.of(context).size.height - MediaQuery.of(context).padding.top,
                ),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween, // Distribute space between children
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    // Top content
                    Column(
                      children: [
                        // Logo at the very top
                        Padding(
                          padding: const EdgeInsets.only(top: 20.0),
                          child: Image.asset(
                            'assets/images/log.png',
                            width: 400, // Increased logo width
                            height: 120, // Increased logo height
                            fit: BoxFit.contain,
                          ),
                        ),
                        const SizedBox(height: 20),
                        // Title container
                        Container(
                          alignment: Alignment.center,
                          padding: const EdgeInsets.symmetric(vertical: 10),
                          color: Colors.blueGrey[50]?.withOpacity(0.8),
                          child: Text(
                            "الدليل الهاتفي للمديرية الإقليمية الحسيمة",
                            style: TextStyle(
                              color: Colors.black87,
                              fontSize: textSize,
                              fontWeight: FontWeight.bold,
                              fontFamily: '4_3D', // Utilisation de la police personnalisée
                            ),
                            textAlign: TextAlign.center,
                          ),
                        ),
                        const SizedBox(height: 20),
                        // Main buttons
                        ...buttonColors.keys.map((label) {
                          String sheetName = ''; // Add your sheet name mapping logic
                          Color bgColor = Colors.white;
                          Color iconColor = Colors.blue;

                          switch (label) {
                            case 'مصالح المديرية':  // When this button is pressed
                              return Padding(
                                padding: const EdgeInsets.symmetric(vertical: 5.0),
                                child: SizedBox(
                                  width: buttonWidth,
                                  height: buttonHeight,
                                  child: ElevatedButton(
                                    onPressed: () {
                                      // Navigate to the Direction Overview view
                                      Navigator.push(
                                        context,
                                        MaterialPageRoute(
                                          builder: (context) => const DirectionOverviewView(),
                                        ),
                                      );
                                    },
                                    style: ElevatedButton.styleFrom(
                                      backgroundColor: buttonColors[label],
                                      shape: RoundedRectangleBorder(
                                        borderRadius: BorderRadius.circular(12),
                                      ),
                                      elevation: 6,
                                    ),
                                    child: Text(
                                      label,
                                      style: TextStyle(
                                        color: Colors.white,
                                        fontSize: textSize,
                                        fontFamily: '4_3D', // Utilisation de la police personnalisée
                                      ),
                                    ),
                                  ),
                                ),
                              );
                            case 'أطر التفتيش والتوجيه':  
                              return Padding(
                                padding: const EdgeInsets.symmetric(vertical: 5.0),
                                child: SizedBox(
                                  width: buttonWidth,
                                  height: buttonHeight,
                                  child: ElevatedButton(
                                    onPressed: () {
                                      // Navigate to the Inspector Overview view
                                      Navigator.push(
                                        context,
                                        MaterialPageRoute(
                                          builder: (context) => const InspectorOverview(),
                                        ),
                                      );
                                    },
                                    style: ElevatedButton.styleFrom(
                                      backgroundColor: buttonColors[label],
                                      shape: RoundedRectangleBorder(
                                        borderRadius: BorderRadius.circular(12),
                                      ),
                                      elevation: 6,
                                    ),
                                    child: Text(
                                      label,
                                      style: TextStyle(
                                        color: Colors.white,
                                        fontSize: textSize,
                                        fontFamily: '4_3D', // Utilisation de la police personnalisée
                                      ),
                                    ),
                                  ),
                                ),
                              );
                            case 'التعليم الإبتدائي':
                              sheetName = 'primaire'; 
                              bgColor = Colors.green[50]!;
                              iconColor = Colors.green;
                              break;
                            case 'الثانوي الإعدادي':
                              sheetName = 'college';
                              bgColor = Colors.orange[50]!;
                              iconColor = Colors.orange;
                              break;
                            case 'الثانوي التأهيلي':
                              sheetName = 'lycee'; 
                              bgColor = Colors.cyan[50]!;
                              iconColor = Colors.cyan;
                              break;
                          }
                          return Padding(
                            padding: const EdgeInsets.symmetric(vertical: 5.0),
                            child: SizedBox(
                              width: buttonWidth,
                              height: buttonHeight,
                              child: ElevatedButton(
                                onPressed: () {
                                  Navigator.push(
                                    context,
                                    MaterialPageRoute(
                                      builder: (context) => SchoolContactsView(
                                        sheetName: sheetName,
                                        title: label,
                                        bgColor: bgColor,
                                        iconColor: iconColor,
                                      ),
                                    ),
                                  );
                                },
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: buttonColors[label],
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                  elevation: 6,
                                ),
                                child: Text(
                                  label,
                                  style: TextStyle(
                                    color: Colors.white,
                                    fontSize: textSize,
                                    fontFamily: '4_3D', // Utilisation de la police personnalisée
                                  ),
                                ),
                              ),
                            ),
                          );
                        }).toList(),

                        const SizedBox(height: 10),
                        // Show progress bar or message
                        if (_isLoading)
                          Padding(
                            padding: const EdgeInsets.symmetric(vertical: 10.0),
                            child: SizedBox(
                              width: buttonWidth - 20, // Progress bar slightly smaller than button
                              child: const LinearProgressIndicator(
                                backgroundColor: Colors.grey,
                                color: Colors.green,
                                minHeight: 6.0,
                              ),
                            ),
                          )
                        else if (_message != null)
                          Padding(
                            padding: const EdgeInsets.symmetric(vertical: 10.0),
                            child: Text(
                              _message!,
                              style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                                color: _messageColor ?? Colors.black, // Use message color if defined
                                fontFamily: '4_3D', // Utilisation de la police personnalisée
                              ),
                              textAlign: TextAlign.center,
                            ),
                          ),
                        // Update button (last button)
                        const SizedBox(height: 10),
                        SizedBox(
                          width: buttonWidth - 60, // Reduced width of the last button
                          height: buttonHeight,
                          child: ElevatedButton(
                            onPressed: _isLoading ? null : _updateData,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.pinkAccent, // Changed color of the last button
                              foregroundColor: Colors.white,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(8),
                              ),
                              elevation: 5,
                            ),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                const Icon(Icons.refresh, color: Colors.white),
                                const SizedBox(width: 10),
                                Text(
                                  'تحديث البيانات',
                                  style: TextStyle(
                                    fontSize: textSize,
                                    fontWeight: FontWeight.bold,
                                    fontFamily: '4_3D', // Utilisation de la police personnalisée
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(height: 20),
                      ],
                    ),
                    // Bottom image
                    Padding(
                      padding: const EdgeInsets.only(bottom: 10.0),
                      child: Image.asset(
                        'assets/images/mdrs.png',
                        width: 150, // Adjust the width as needed
                        fit: BoxFit.contain,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
