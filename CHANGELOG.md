# CHANGELOG


## v1.1.2 (2024-12-09)

### Bug Fixes

- Wrong type check
  ([`e585005`](https://github.com/beatreichenbach/qt-extensions/commit/e585005e117cbda65f13c860c49de98042b97b1d))

### Build System

- Update release action
  ([`d00db89`](https://github.com/beatreichenbach/qt-extensions/commit/d00db890bbd041c749db5b4a21db52959a620d00))

- Update semantic-release
  ([`13d316d`](https://github.com/beatreichenbach/qt-extensions/commit/13d316d72b287ece214528400eccbda646accc37))

### Documentation

- Update screenshot links
  ([`bbd7ffb`](https://github.com/beatreichenbach/qt-extensions/commit/bbd7ffb4164e9d5b53d6fb3e3c61e941d8d2860f))


## v1.1.1 (2024-11-17)

### Bug Fixes

- **messagebox**: Remove default icons on standardbuttons
  ([`4d4865d`](https://github.com/beatreichenbach/qt-extensions/commit/4d4865d55278f7b5ff5b80fe93d30d753d99b0b1))

- **parameters**: Disable label on checkable params
  ([`1eaf814`](https://github.com/beatreichenbach/qt-extensions/commit/1eaf814f0eaacbdca92ec6ebdc3f1fbbb8e1e49d))

- **parameters**: Remove text widget on StringParameter
  ([`571f31c`](https://github.com/beatreichenbach/qt-extensions/commit/571f31cbe6bbc5e5d738260f946a6bb0f9c73621))

- **parameters**: Restructure add_param for tab order
  ([`a9a6099`](https://github.com/beatreichenbach/qt-extensions/commit/a9a6099532e1e41444b7bccd517a0ed675eeb49d))

### Chores

- Remove print statements
  ([`150db30`](https://github.com/beatreichenbach/qt-extensions/commit/150db309ad60fd532a5c47d59619aa6ee8d7e857))


## v1.1.0 (2024-11-06)

### Features

- **parameters**: Add label widget
  ([`aa6f144`](https://github.com/beatreichenbach/qt-extensions/commit/aa6f144b8e8aad97606fb655e6d68988bcd8c7ee))


## v1.0.0 (2024-10-04)

### Bug Fixes

- **box**: Make title optional
  ([`ccaf3fc`](https://github.com/beatreichenbach/qt-extensions/commit/ccaf3fc4b6288a1c25d0255603802b04a8cdecd6))

- **logger**: Escape html tags
  ([`c5423b1`](https://github.com/beatreichenbach/qt-extensions/commit/c5423b12b68cc6edba80e4339dfb3d0e2a5b1b59))

- **paramaters**: Remove editor layout margins
  ([`c14c2bb`](https://github.com/beatreichenbach/qt-extensions/commit/c14c2bbc1ad632c645411d625ec64db0540878a7))

- **parameters**: Bugs
  ([`130e737`](https://github.com/beatreichenbach/qt-extensions/commit/130e73721b01ebd84ed329100cf6aca57d45c460))

### Chores

- Add black
  ([`97e547d`](https://github.com/beatreichenbach/qt-extensions/commit/97e547d9efc8376cac0da36aa0f0c749b923dc9c))

### Code Style

- Add type hints
  ([`a48d77b`](https://github.com/beatreichenbach/qt-extensions/commit/a48d77b489c1779eb0b72c3aa1267a9986f12b42))

- Docstring
  ([`cfb2b16`](https://github.com/beatreichenbach/qt-extensions/commit/cfb2b168676720a718a1c73b202b5581c73bcf02))

- **button**: Cleanup unused code
  ([`9d802fb`](https://github.com/beatreichenbach/qt-extensions/commit/9d802fb741b43fbc08fed78c309094ce8b99db36))

### Documentation

- Restructure
  ([`7549bb5`](https://github.com/beatreichenbach/qt-extensions/commit/7549bb5fb6d3bfbb5c1f88ce842c92b835b357d9))

- Update contributing
  ([`449fede`](https://github.com/beatreichenbach/qt-extensions/commit/449fede56296f2665ce94158cc4ccda7fc815b2e))

### Features

- **box**: Expose title
  ([`bbcd870`](https://github.com/beatreichenbach/qt-extensions/commit/bbcd87084e35a554f932eecf15f32cb23b1596fd))

- **icons**: Remove icons
  ([`ba42afb`](https://github.com/beatreichenbach/qt-extensions/commit/ba42afbc647795adb8b29574abf39b4f19911be7))

BREAKING CHANGE: icons are no longer accessible.

- **icons**: Remove submodule
  ([`56c5361`](https://github.com/beatreichenbach/qt-extensions/commit/56c536195dd0a9fbbe690325fd170472097e230f))

- **icons**: Update material symbols
  ([`9b5ffc8`](https://github.com/beatreichenbach/qt-extensions/commit/9b5ffc8027c6e99584f12e1cea639c1f03a6b967))

BREAKING CHANGE: remove size parameter

- **theme**: Add one_dark_two
  ([`702bfa6`](https://github.com/beatreichenbach/qt-extensions/commit/702bfa674f021e473d12582cf239c88e73b234a1))

- **widgets**: Add combo parameter
  ([`abc34d2`](https://github.com/beatreichenbach/qt-extensions/commit/abc34d2721a3273a314156635100d1680858712c))

### Refactoring

- Simplify logger
  ([`c2255e4`](https://github.com/beatreichenbach/qt-extensions/commit/c2255e4945caae8f43e97bf4d7db2fefe46227a4))

- Typing
  ([`5a2555c`](https://github.com/beatreichenbach/qt-extensions/commit/5a2555c9297a99b42f79971d238fd74eaf21ea5d))

- **mainwindow**: Types
  ([`1c1b943`](https://github.com/beatreichenbach/qt-extensions/commit/1c1b943155743eb4b8331d3b78333356304b52b2))

- **typeutils**: Better type hints
  ([`521b41e`](https://github.com/beatreichenbach/qt-extensions/commit/521b41ec8b38b21a2dc43b7ec760653fc7cb81e2))

- **widgets**: Types
  ([`93bd341`](https://github.com/beatreichenbach/qt-extensions/commit/93bd3412bc9eab852ff53d862bceafb1df9123a6))

### Testing

- Add wrapper
  ([`f1fb891`](https://github.com/beatreichenbach/qt-extensions/commit/f1fb891532172f91d3d20fbb88bdc3335741dd38))

- Clean up
  ([`b296f76`](https://github.com/beatreichenbach/qt-extensions/commit/b296f760cb972fd5d79a7e2b23ffd0c7f9030493))

### BREAKING CHANGES

- **icons**: Icons are no longer accessible.


## v0.4.3 (2024-07-16)

### Bug Fixes

- Add cache to logbar
  ([`b5db9f5`](https://github.com/beatreichenbach/qt-extensions/commit/b5db9f5510d091863251d71d300b131f00686ec0))


## v0.4.2 (2024-07-16)

### Bug Fixes

- Type checking
  ([`3ebf66f`](https://github.com/beatreichenbach/qt-extensions/commit/3ebf66fd257d82fa139612466367a85241a3cf1d))


## v0.4.1 (2024-07-16)

### Bug Fixes

- Add cast for lists
  ([`46aae30`](https://github.com/beatreichenbach/qt-extensions/commit/46aae3086ef4666e9ac6587f98c59d6be471c3c2))

- Expose cache
  ([`2360e5c`](https://github.com/beatreichenbach/qt-extensions/commit/2360e5c031ae43317134d18f9a0d68ff55c03cca))


## v0.4.0 (2024-06-10)

### Bug Fixes

- Remove typing_extensions dependency
  ([`41aa269`](https://github.com/beatreichenbach/qt-extensions/commit/41aa269b942ce667811f328eea0ff24bee838bbc))

- **button**: Change text based on color
  ([`3db1893`](https://github.com/beatreichenbach/qt-extensions/commit/3db1893678e7946e2ad656cb18d399e818a7e065))

- **logger**: Expose size_grip
  ([`8c146ee`](https://github.com/beatreichenbach/qt-extensions/commit/8c146ee0f99759a3fafd3c306036e7251036c4af))

### Chores

- Add icons screenshot and test
  ([`68dabad`](https://github.com/beatreichenbach/qt-extensions/commit/68dabad37dfea3e8b0239f617702fed38ef48945))

- Cleanup
  ([`e27296d`](https://github.com/beatreichenbach/qt-extensions/commit/e27296de935a2d10cb1351d3e931ea509a3fa9fd))

### Documentation

- Update instructions
  ([`ba04508`](https://github.com/beatreichenbach/qt-extensions/commit/ba0450858434186696a2567cf2e7ce38413c88e2))

### Features

- **logger**: Add success level
  ([`181771c`](https://github.com/beatreichenbach/qt-extensions/commit/181771c2014aa4887eca84c5602d9ff2f930a4d6))

### Testing

- **viewer**: Remove unused roles from test
  ([`5a7b21d`](https://github.com/beatreichenbach/qt-extensions/commit/5a7b21d894d5f6bfe54e6fb0c0feb2dac3d7cc71))


## v0.3.0 (2024-05-23)

### Bug Fixes

- Update release
  ([`f844430`](https://github.com/beatreichenbach/qt-extensions/commit/f844430661114e3a4bcfe0f4bcf29bd68832ab80))

- **logger**: Check record validity
  ([`8eb20ca`](https://github.com/beatreichenbach/qt-extensions/commit/8eb20ca047b7895c0566e425e6da24b6d6deb3b3))

- **parameters**: Hide slider
  ([`b7211f5`](https://github.com/beatreichenbach/qt-extensions/commit/b7211f5546d62b86eef9a38507152d41e8cfe9c3))

### Chores

- Create LICENSE
  ([`010962b`](https://github.com/beatreichenbach/qt-extensions/commit/010962ba927c55a0dbacdf56e4937177bbadc768))

### Features

- Add pypi worklflow
  ([`2965384`](https://github.com/beatreichenbach/qt-extensions/commit/29653849557da97d2eea3f4168bf18747053114b))

- Update semantic release
  ([`1f382f5`](https://github.com/beatreichenbach/qt-extensions/commit/1f382f5547b71753d04f54c4f5682d9d27512b79))

- **parameters**: Add multi number parameters
  ([`2f259b9`](https://github.com/beatreichenbach/qt-extensions/commit/2f259b94ec25b9be03f0fe3f245b225b0cf6528c))

- **viewer**: Add channels
  ([`c4e6685`](https://github.com/beatreichenbach/qt-extensions/commit/c4e66851843f796a7454973d8f35283189c58755))


## v0.2.0 (2023-07-02)

### Bug Fixes

- **editor**: Connect reset action in tests
  ([`327967b`](https://github.com/beatreichenbach/qt-extensions/commit/327967b028d1d22b2640efb4115b1004f8323b51))

- **scrollarea**: Make background transparent
  ([`ff0a3c6`](https://github.com/beatreichenbach/qt-extensions/commit/ff0a3c62a7d9b6f35f7421384a0937527b1eb3e3))

### Features

- Replace properties with setter functions
  ([`326f8c9`](https://github.com/beatreichenbach/qt-extensions/commit/326f8c9f39c1261f1a1bf007cc02f008ca388728))


## v0.1.4 (2023-06-19)

### Bug Fixes

- **parameters**: Keep_ratio toggle
  ([`5c97bad`](https://github.com/beatreichenbach/qt-extensions/commit/5c97bad3dea1eed43bb60d6f634f85676b5582f5))

- **parameters**: Ratio typos
  ([`d7db65b`](https://github.com/beatreichenbach/qt-extensions/commit/d7db65bdfdccbb62100d5ad5ec3a08dd1091fd94))

- **viewer**: Ignore empty images
  ([`f888d11`](https://github.com/beatreichenbach/qt-extensions/commit/f888d110210d93179a6853df2496c15a33e55170))

### Refactoring

- **parameters**: Cleanup
  ([`0c74583`](https://github.com/beatreichenbach/qt-extensions/commit/0c74583d0516008c810c13a1c1d11f20af76830e))


## v0.1.3 (2023-06-01)

### Bug Fixes

- **typeutils**: Don't cast existing enums
  ([`07a8943`](https://github.com/beatreichenbach/qt-extensions/commit/07a8943f267de78371b66547c8e753bf34d6474a))

- **viewer**: Trigger fit to view
  ([`761fcd7`](https://github.com/beatreichenbach/qt-extensions/commit/761fcd766f996eb3f32ff355d0215fc20327d015))


## v0.1.2 (2023-05-26)

### Bug Fixes

- Make python 3.9 compatible
  ([`d217fae`](https://github.com/beatreichenbach/qt-extensions/commit/d217fae17b4f8152e7798f94a60ca0dc2345f858))

- **viewer**: Clean up
  ([`cd94323`](https://github.com/beatreichenbach/qt-extensions/commit/cd94323be908463508e9cfba5ec20e9900658a13))

- **viewer**: Inverted pixel position
  ([`0b5494a`](https://github.com/beatreichenbach/qt-extensions/commit/0b5494a8ff54251552be79b1b82be204a82b52c1))


## v0.1.1 (2023-05-21)

### Bug Fixes

- **logger**: Avoid multiple cache connections
  ([`3803f8c`](https://github.com/beatreichenbach/qt-extensions/commit/3803f8c2104e8038f1d1fc2201d99ac7d561282e))

- **mainwindow**: Set geometry
  ([`3436b29`](https://github.com/beatreichenbach/qt-extensions/commit/3436b2914bfa1cf7654157b6715badff1f7475fe))

### Code Style

- **viewer**: Fix typos
  ([`01d2b5c`](https://github.com/beatreichenbach/qt-extensions/commit/01d2b5c0d2223384f39981be816dd59b31d468fe))


## v0.1.0 (2023-05-20)

### Bug Fixes

- Various typos
  ([`1536a5f`](https://github.com/beatreichenbach/qt-extensions/commit/1536a5f5f449b22801df22cecdf17293fe575f4e))

- **editor**: Add support for nested boxes
  ([`8a3e96b`](https://github.com/beatreichenbach/qt-extensions/commit/8a3e96badf519c52d9d10280197d7415a10843a9))

- **logger**: Remove focus policy from toolbar
  ([`188123e`](https://github.com/beatreichenbach/qt-extensions/commit/188123eb86615a78e96c0f897743a3f88c2764c5))

- **logger**: Set defaults
  ([`90ab735`](https://github.com/beatreichenbach/qt-extensions/commit/90ab73561a7ff1ef9391f922da6773097330b587))

- **parameters**: Default for enum values
  ([`b0da63e`](https://github.com/beatreichenbach/qt-extensions/commit/b0da63e359da18bf262c01d752ef103e213b323f))

### Code Style

- Rename prop to parm
  ([`fad5e84`](https://github.com/beatreichenbach/qt-extensions/commit/fad5e84b5f3674d30764cf3cd6c82f1a0b776989))

### Documentation

- Change parameter, update screenshots and add logger
  ([`5547b7e`](https://github.com/beatreichenbach/qt-extensions/commit/5547b7e66e653f1984dccd939599e83d022b6d74))

### Features

- **buttons**: Add icon, color to button
  ([`5e903f8`](https://github.com/beatreichenbach/qt-extensions/commit/5e903f887b0538e8cc66672cf1d0ef223e7b77dd))

- **editor**: Add support for checkable parms
  ([`5372e24`](https://github.com/beatreichenbach/qt-extensions/commit/5372e245cab4f46f1713e25ff9989d520a0824bf))

- **enum**: Fix enum parameter bugs and editor cleanup
  ([`269eb62`](https://github.com/beatreichenbach/qt-extensions/commit/269eb625f74ad5ed719b0d3bbeba7154a8c5d63e))

- **icons**: Add color and size support
  ([`22bde5d`](https://github.com/beatreichenbach/qt-extensions/commit/22bde5d594e9a2d564d28bf85294f47bd2d426c1))

- **logger**: Add logger
  ([`7c8393c`](https://github.com/beatreichenbach/qt-extensions/commit/7c8393c3bf87015a717dd5e33c88226c6a4960a7))

- **logger**: Add logger
  ([`73594dc`](https://github.com/beatreichenbach/qt-extensions/commit/73594dc8a6fc33808aebc2748806c66fc32b8912))

- **typeutils**: Add deep_field
  ([`d5f428f`](https://github.com/beatreichenbach/qt-extensions/commit/d5f428fd6311a688e03712c2b78b53fc38087b69))

### Performance Improvements

- **typeutils**: Caching for hashable dataclasses
  ([`15dd998`](https://github.com/beatreichenbach/qt-extensions/commit/15dd9988408ca49fedc41684a9ef8709ef8e5c85))

### Refactoring

- Use logger instead of logging
  ([`ed27ac4`](https://github.com/beatreichenbach/qt-extensions/commit/ed27ac4eeb51afbd7713384a0d8c89a3e8067746))

- Use setter functions
  ([`5335b9a`](https://github.com/beatreichenbach/qt-extensions/commit/5335b9a50d5a97a6fd9ecb9ff1223c0322240055))

- Various
  ([`002fc79`](https://github.com/beatreichenbach/qt-extensions/commit/002fc790772e30f43a4ae4bb1a3557dc520e290c))

- **editor**: Simplify widget states (use dicts)
  ([`e02458a`](https://github.com/beatreichenbach/qt-extensions/commit/e02458af8e3fe850a15195ee46ded9b93dd74c9e))

- **icons**: Add set_color
  ([`67d3c85`](https://github.com/beatreichenbach/qt-extensions/commit/67d3c855c070e972087e553774b7dbd9ce68ce63))

- **parameters**: Rename properties to parameters
  ([`7c8c938`](https://github.com/beatreichenbach/qt-extensions/commit/7c8c938cd9bffeb93f41c4afc5d49903eca2f0e5))

- **theme**: New color scheme system that works for dark and light
  ([`1333dc2`](https://github.com/beatreichenbach/qt-extensions/commit/1333dc213c9b1758611483f4ce11427e06a607d3))


## v0.0.2 (2023-04-30)

### Refactoring

- Cleanup
  ([`c7aae30`](https://github.com/beatreichenbach/qt-extensions/commit/c7aae309720a0f73db3bf1c19316bf6a711a67e8))

- **box**: Make title editable
  ([`94eb4aa`](https://github.com/beatreichenbach/qt-extensions/commit/94eb4aa6ff456c84ca3084552aacb4bf28a5c2ea))

- **typeutils**: Simplify cast
  ([`fcb9d4b`](https://github.com/beatreichenbach/qt-extensions/commit/fcb9d4b03ff0f7a3d4a1c7bcc5e5cef945d035af))


## v0.0.1 (2023-04-28)

### Build System

- Add python-semantic-release
  ([`de57414`](https://github.com/beatreichenbach/qt-extensions/commit/de57414a3044a984f3f9103d7ca83a0f4c4696d1))

### Features

- Add exposure toggle
  ([`09138ea`](https://github.com/beatreichenbach/qt-extensions/commit/09138ea0fa41c2dafde54c97dbfd4cf74b15077d))
