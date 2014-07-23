===== ======= ======= =========== ======== ==== =========  =====================  ========================  =========================  ============================  ================================
index bar.spt bar.txt bar.txt.spt %bar.spt bar/ bar/index  /                      /bar                      /bar/                      /bar.txt                      /bar.txt/
===== ======= ======= =========== ======== ==== =========  =====================  ========================  =========================  ============================  ================================
  #   1 file
  X      _       _         _          _      _      _      200 index              404                       404                        404                           404                            
  _      X       _         _          _      _      _      404*                   200 bar.spt               404                        200 bar.spt                   404
  _      _       X         _          _      _      _      404*                   404                       404                        200 bar.txt                   404
  _      _       _         X          _      _      _      404*                   404                       404                        200 bar.txt.spt               404
  _      _       _         _          X      _      _      200 %bar.spt (bar='')  200 %bar.spt (bar='bar')  200 %bar.spt (bar='bar/')  200 %bar.spt (bar='bar.txt')  200 %bar.spt (bar='bar.txt/')
  _      _       _         _          _      X      _      404*                   302 /bar/                 404*                       404                           404
  _      _       _         _          _      _      X      404*                   302 /bar/                 200 bar/index              404                           404
  #   2 files
  X      X       _         _          _      _      _      200 index              200 bar.spt               404                        200 bar.spt                   404
  X      _       X         _          _      _      _      200 index              404                       404                        200 bar.txt                   404
  X      _       _         X          _      _      _      200 index              404                       404                        200 bar.txt.spt               404
  X      _       _         _          X      _      _      200 index              200 %bar.spt (bar='bar')  200 %bar.spt (bar='bar/')  200 %bar.spt (bar='bar.txt')  200 %bar.spt (bar='bar.txt/')
  X      _       _         _          _      X      _      200 index              302 /bar/                 404*                       404                           404
  X      _       _         _          _      _      X      200 index              302 /bar/                 200 bar/index              404                           404
  _      X       X         _          _      _      _      404*                   200 bar.spt               404                        200 bar.txt                   404
  _      X       _         X          _      _      _      404*                   200 bar.spt               404                        200 bar.txt.spt               404
  _      X       _         _          X      _      _      200 %bar.spt (bar='')  200 bar.spt               200 %bar.spt (bar='bar/')  200 bar.spt                   200 %bar.spt (bar='bar.txt/')
  _      X       _         _          _      X      _      404*                   200 bar.spt               404*                       200 bar.spt                   404
  _      X       _         _          _      _      X      404*                   200 bar.spt               200 bar/index              200 bar.spt                   404
  _      _       X         X          _      _      _      404*                   404                       404                        200 bar.txt                   404
  _      _       X         _          X      _      _      200 %bar.spt (bar='')  200 %bar.spt (bar='bar')  200 %bar.spt (bar='bar/')  200 bar.txt                   200 %bar.spt (bar='bar.txt/')
  _      _       X         _          _      X      _      404*                   302 /bar/                 404*                       200 bar.txt                   404
  _      _       X         _          _      _      X      404*                   302 /bar/                 200 bar/index              200 bar.txt                   404
  _      _       _         X          X      _      _      200 %bar.spt (bar='')  200 %bar.spt (bar='bar')  200 %bar.spt (bar='bar/')  200 bar.txt.spt               200 %bar.spt (bar='bar.txt/')
  _      _       _         X          _      X      _      404*                   302 /bar/                 404*                       200 bar.txt.spt               404
  _      _       _         X          _      _      X      404*                   302 /bar/                 200 bar/index              200 bar.txt.spt               404
  _      _       _         _          X      X      _      200 %bar.spt (bar='')  302 /bar/                 404*                       200 %bar.spt (bar='bar.txt')  200 %bar.spt (bar='bar.txt/')
  _      _       _         _          X      _      X      200 %bar.spt (bar='')  302 /bar/                 200 bar/index              200 %bar.spt (bar='bar.txt')  200 %bar.spt (bar='bar.txt/')
#==== ======= ======= =========== ======== ==== =========  =====================  ========================  =========================  ============================  ================================
#ndex bar.spt bar.txt bar.txt.spt %bar.spt bar/ bar/index  /                      /bar                      /bar/                      /bar.txt                      /bar.txt/
#==== ======= ======= =========== ======== ==== =========  =====================  ========================  =========================  ============================  ================================
  #   3 files
  X      X       X         _          _      _      _      200 index              200 bar.spt               404                        200 bar.txt                   404
  X      X       _         X          _      _      _      200 index              200 bar.spt               404                        200 bar.txt.spt               404
  X      X       _         _          X      _      _      200 index              200 bar.spt               200 %bar.spt (bar='bar/')  200 bar.spt                   200 %bar.spt (bar='bar.txt/')
  X      X       _         _          _      X      _      200 index              200 bar.spt               404*                       200 bar.spt                   404
  X      X       _         _          _      _      X      200 index              200 bar.spt               200 bar/index              200 bar.spt                   404
  X      _       X         X          _      _      _      200 index              404                       404                        200 bar.txt                   404
  X      _       X         _          X      _      _      200 index              200 %bar.spt (bar='bar')  200 %bar.spt (bar='bar/')  200 bar.txt                   200 %bar.spt (bar='bar.txt/')
  X      _       X         _          _      X      _      200 index              302 /bar/                 404*                       200 bar.txt                   404
  X      _       X         _          _      _      X      200 index              302 /bar/                 200 bar/index              200 bar.txt                   404
  X      _       _         X          X      _      _      200 index              200 %bar.spt (bar='bar')  200 %bar.spt (bar='bar/')  200 bar.txt.spt               200 %bar.spt (bar='bar.txt/')
  X      _       _         X          _      X      _      200 index              302 /bar/                 404*                       200 bar.txt.spt               404
  X      _       _         X          _      _      X      200 index              302 /bar/                 200 bar/index              200 bar.txt.spt               404
  X      _       _         _          X      X      _      200 index              302 /bar/                 404*                       200 %bar.spt (bar='bar.txt')  200 %bar.spt (bar='bar.txt/')
  X      _       _         _          X      _      X      200 index              302 /bar/                 200 bar/index              200 %bar.spt (bar='bar.txt')  200 %bar.spt (bar='bar.txt/')
  _      X       X         X          _      _      _      404*                   200 bar.spt               404                        200 bar.txt                   404
  _      X       X         _          X      _      _      200 %bar.spt (bar='')  200 bar.spt               200 %bar.spt (bar='bar/')  200 bar.txt                   200 %bar.spt (bar='bar.txt/')
  _      X       X         _          _      X      _      404*                   200 bar.spt               404*                       200 bar.txt                   404
  _      X       X         _          _      _      X      404*                   200 bar.spt               200 bar/index              200 bar.txt                   404
  _      X       _         X          X      _      _      200 %bar.spt (bar='')  200 bar.spt               200 %bar.spt (bar='bar/')  200 bar.txt.spt               200 %bar.spt (bar='bar.txt/')
  _      X       _         X          _      X      _      404*                   200 bar.spt               404*                       200 bar.txt.spt               404
  _      X       _         X          _      _      X      404*                   200 bar.spt               200 bar/index              200 bar.txt.spt               404
  _      X       _         _          X      X      _      200 %bar.spt (bar='')  200 bar.spt               404*                       200 bar.spt                   200 %bar.spt (bar='bar.txt/')
  _      X       _         _          X      _      X      200 %bar.spt (bar='')  200 bar.spt               200 bar/index              200 bar.spt                   200 %bar.spt (bar='bar.txt/')
  _      _       X         X          X      _      _      200 %bar.spt (bar='')  200 %bar.spt (bar='bar')  200 %bar.spt (bar='bar/')  200 bar.txt                   200 %bar.spt (bar='bar.txt/')
  _      _       X         X          _      X      _      404*                   302 /bar/                 404*                       200 bar.txt                   404
  _      _       X         X          _      _      X      404*                   302 /bar/                 200 bar/index              200 bar.txt                   404
  _      _       X         _          X      X      _      200 %bar.spt (bar='')  302 /bar/                 404*                       200 bar.txt                   200 %bar.spt (bar='bar.txt/')
  _      _       X         _          X      _      X      200 %bar.spt (bar='')  302 /bar/                 200 bar/index              200 bar.txt                   200 %bar.spt (bar='bar.txt/')
  _      _       _         X          X      X      _      200 %bar.spt (bar='')  302 /bar/                 404*                       200 bar.txt.spt               200 %bar.spt (bar='bar.txt/')
  _      _       _         X          X      _      X      200 %bar.spt (bar='')  302 /bar/                 200 bar/index              200 bar.txt.spt               200 %bar.spt (bar='bar.txt/')
#==== ======= ======= =========== ======== ==== =========  =====================  ========================  =========================  ============================  ================================
#ndex bar.spt bar.txt bar.txt.spt %bar.spt bar/ bar/index  /                      /bar                      /bar/                      /bar.txt                      /bar.txt/
#==== ======= ======= =========== ======== ==== =========  =====================  ========================  =========================  ============================  ================================
  #   4 files
  X      X       X         X          _      _      _      200 index              200 bar.spt               404                        200 bar.txt                   404
  X      X       X         _          X      _      _      200 index              200 bar.spt               200 %bar.spt (bar='bar/')  200 bar.txt                   200 %bar.spt (bar='bar.txt/')
  X      X       X         _          _      X      _      200 index              200 bar.spt               404*                       200 bar.txt                   404
  X      X       X         _          _      _      X      200 index              200 bar.spt               200 bar/index              200 bar.txt                   404
  X      X       _         X          X      _      _      200 index              200 bar.spt               200 %bar.spt (bar='bar/')  200 bar.txt.spt               200 %bar.spt (bar='bar.txt/')
  X      X       _         X          _      X      _      200 index              200 bar.spt               404*                       200 bar.txt.spt               404
  X      X       _         X          _      _      X      200 index              200 bar.spt               200 bar/index              200 bar.txt.spt               404
  X      X       _         _          X      X      _      200 index              200 bar.spt               404*                       200 bar.spt                   200 %bar.spt (bar='bar.txt/')
  X      X       _         _          X      _      X      200 index              200 bar.spt               200 bar/index              200 bar.spt                   200 %bar.spt (bar='bar.txt/')
  X      _       X         X          X      _      _      200 index              200 %bar.spt (bar='bar')  200 %bar.spt (bar='bar/')  200 bar.txt                   200 %bar.spt (bar='bar.txt/')
  X      _       X         X          _      X      _      200 index              302 /bar/                 404*                       200 bar.txt                   404
  X      _       X         X          _      _      X      200 index              302 /bar/                 200 bar/index              200 bar.txt                   404
  X      _       X         _          X      X      _      200 index              302 /bar/                 404*                       200 bar.txt                   200 %bar.spt (bar='bar.txt/')
  X      _       X         _          X      _      X      200 index              302 /bar/                 200 bar/index              200 bar.txt                   200 %bar.spt (bar='bar.txt/')
  X      _       _         X          X      X      _      200 index              302 /bar/                 404*                       200 bar.txt.spt               200 %bar.spt (bar='bar.txt/')
  X      _       _         X          X      _      X      200 index              302 /bar/                 200 bar/index              200 bar.txt.spt               200 %bar.spt (bar='bar.txt/')
  -      X       X         X          X      _      _      200 %bar.spt (bar='')  200 bar.spt               200 %bar.spt (bar='bar/')  200 bar.txt                   200 %bar.spt (bar='bar.txt/')
  -      X       X         X          _      X      _      404*                   200 bar.spt               404*                       200 bar.txt                   404
  -      X       X         X          _      _      X      404*                   200 bar.spt               200 bar/index              200 bar.txt                   404
  -      X       _         X          X      X      _      200 %bar.spt (bar='')  200 bar.spt               404*                       200 bar.txt.spt               200 %bar.spt (bar='bar.txt/')
  -      X       _         X          X      _      X      200 %bar.spt (bar='')  200 bar.spt               200 bar/index              200 bar.txt.spt               200 %bar.spt (bar='bar.txt/')
  -      _       X         X          X      X      _      200 %bar.spt (bar='')  302 /bar/                 404*                       200 bar.txt                   200 %bar.spt (bar='bar.txt/')
  -      _       X         X          X      _      X      200 %bar.spt (bar='')  302 /bar/                 200 bar/index              200 bar.txt                   200 %bar.spt (bar='bar.txt/')
  #   5 files
  X      X       X         X          X      _      _      200 index              200 bar.spt               200 %bar.spt (bar='bar/')  200 bar.txt                   200 %bar.spt (bar='bar.txt/')
  X      X       X         X          _      X      _      200 index              200 bar.spt               404*                       200 bar.txt                   404
  X      X       X         X          _      _      X      200 index              200 bar.spt               200 bar/index              200 bar.txt                   404
  X      X       X         _          X      X      _      200 index              200 bar.spt               404*                       200 bar.txt                   200 %bar.spt (bar='bar.txt/')
  X      X       X         _          X      _      X      200 index              200 bar.spt               200 bar/index              200 bar.txt                   200 %bar.spt (bar='bar.txt/')
  X      X       _         X          X      X      _      200 index              200 bar.spt               404                        200 bar.txt.spt               200 %bar.spt (bar='bar.txt/')
  X      X       _         X          X      _      X      200 index              200 bar.spt               200 bar/index              200 bar.txt.spt               200 %bar.spt (bar='bar.txt/')
  X      _       X         X          X      X      _      200 index              302 /bar/                 404*                       200 bar.txt                   200 %bar.spt (bar='bar.txt/')
  X      _       X         X          X      _      X      200 index              302 /bar/                 200 bar/index              200 bar.txt                   200 %bar.spt (bar='bar.txt/')
  _      X       X         X          X      X      _      200 %bar.spt (bar='')  200 bar.spt               404*                       200 bar.txt                   200 %bar.spt (bar='bar.txt/')
  _      X       X         X          X      _      X      200 %bar.spt (bar='')  200 bar.spt               200 bar/index              200 bar.txt                   200 %bar.spt (bar='bar.txt/')
  #   6 files
  X      X       X         X          X      X      _      200 index              200 bar.spt               404*                       200 bar.txt                   200 %bar.spt (bar='bar.txt/')
  X      X       X         X          X      _      X      200 index              200 bar.spt               200 bar/index              200 bar.txt                   200 %bar.spt (bar='bar.txt/')
===== ======= ======= =========== ======== ==== =========  =====================  ========================  =========================  ============================  ================================

Notes:
------

  * Philosophy: 'most specific wins'
    * exact matches beat non-exact matches
    * requesting /foo.html will check/return approximately: foo.html, foo.html.spt, foo.spt, foo.html/, %*.html.spt, %*.spt

  * Note that bar/ and bar/index in the above are mutually exclusive since bar/index implies the existence of bar/
  * There should be 2^5 * 3 lines data lines: on/off for the files except the last two have only 3 possibilites: [ bar/, bar/index, nothing ]

Future work:
============

  * Potentially interesting files:
    * %bar/
    * %bar/index
    * %bar/baz.spt

