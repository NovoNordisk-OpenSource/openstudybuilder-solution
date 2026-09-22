
## Installed packages

| Package            | Version      | License                                  |
|--------------------|--------------|------------------------------------------|
| annotated-doc      | 0.0.5        | [MIT](#annotated-doc)                    |
| annotated-types    | 0.8.0        | [MIT](#annotated-types)                  |
| anyio              | 4.15.1       | [MIT](#anyio)                            |
| beautifulsoup4     | 4.12.3       | [MIT License](#beautifulsoup4)           |
| certifi            | 2026.7.22    | [MPL-2.0](#certifi)                      |
| charset-normalizer | 3.5.1        | [MIT](#charset-normalizer)               |
| coverage           | 7.16.1       | [Apache-2.0](#coverage)                  |
| fastapi            | 0.137.2      | [MIT](#fastapi)                          |
| h11                | 0.16.0       | [MIT](#h11)                              |
| httpcore           | 1.0.9        | [BSD-3-Clause](#httpcore)                |
| httpx              | 0.28.1       | [BSD-3-Clause](#httpx)                   |
| httpx_auth         | 0.23.1       | [see below](#httpx_auth)                 |
| idna               | 3.20         | [BSD-3-Clause](#idna)                    |
| iniconfig          | 2.3.0        | [MIT](#iniconfig)                        |
| Mako               | 1.4.1        | [MIT](#mako)                             |
| MarkupSafe         | 3.0.3        | [BSD-3-Clause](#markupsafe)              |
| neo4j              | 6.1.0        | [Apache-2.0 AND Python-2.0](#neo4j)      |
| neomodel           | 6.1.0        | [MIT](#neomodel)                         |
| packaging          | 26.3         | [Apache-2.0 OR BSD-2-Clause](#packaging) |
| pluggy             | 1.6.0        | [MIT](#pluggy)                           |
| pydantic           | 2.12.5       | [MIT](#pydantic)                         |
| pydantic_core      | 2.41.5       | [MIT](#pydantic_core)                    |
| Pygments           | 2.21.0       | [BSD-2-Clause](#pygments)                |
| pytest             | 9.1.1        | [MIT](#pytest)                           |
| pytest-cov         | 7.0.0        | [MIT](#pytest-cov)                       |
| pytz               | 2026.3.post1 | [MIT](#pytz)                             |
| requests           | 2.34.2       | [Apache-2.0](#requests)                  |
| soupsieve          | 2.9.2        | [MIT](#soupsieve)                        |
| starlette          | 1.6.0        | [BSD-3-Clause](#starlette)               |
| typing_extensions  | 4.16.0       | [PSF-2.0](#typing_extensions)            |
| typing-inspection  | 0.4.4        | [MIT](#typing-inspection)                |
| urllib3            | 2.8.0        | [MIT](#urllib3)                          |


## Third-party package licenses

---
### annotated-doc

    The MIT License (MIT)

    Copyright (c) 2025 Sebastián Ramírez

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.

---
### annotated-types

    The MIT License (MIT)

    Copyright (c) 2022 the contributors

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

---
### anyio

    The MIT License (MIT)

    Copyright (c) 2018 Alex Grönholm

    Permission is hereby granted, free of charge, to any person obtaining a copy of
    this software and associated documentation files (the "Software"), to deal in
    the Software without restriction, including without limitation the rights to
    use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
    the Software, and to permit persons to whom the Software is furnished to do so,
    subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
    FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
    COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
    IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
    CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---
### beautifulsoup4

    Behold, mortal, the origins of Beautiful Soup...
    ================================================

    Leonard Richardson is the primary maintainer.

    Aaron DeVore and Isaac Muse have made significant contributions to the
    code base.

    Mark Pilgrim provided the encoding detection code that forms the base
    of UnicodeDammit.

    Thomas Kluyver and Ezio Melotti finished the work of getting Beautiful
    Soup 4 working under Python 3.

    Simon Willison wrote soupselect, which was used to make Beautiful Soup
    support CSS selectors. Isaac Muse wrote SoupSieve, which made it
    possible to _remove_ the CSS selector code from Beautiful Soup.

    Sam Ruby helped with a lot of edge cases.

    Jonathan Ellis was awarded the prestigious Beau Potage D'Or for his
    work in solving the nestable tags conundrum.

    An incomplete list of people have contributed patches to Beautiful
    Soup:

     Istvan Albert, Andrew Lin, Anthony Baxter, Oliver Beattie, Andrew
    Boyko, Tony Chang, Francisco Canas, "Delong", Zephyr Fang, Fuzzy,
    Roman Gaufman, Yoni Gilad, Richie Hindle, Toshihiro Kamiya, Peteris
    Krumins, Kent Johnson, Marek Kapolka, Andreas Kostyrka, Roel Kramer,
    Ben Last, Robert Leftwich, Stefaan Lippens, "liquider", Staffan
    Malmgren, Ksenia Marasanova, JP Moins, Adam Monsen, John Nagle, "Jon",
    Ed Oskiewicz, Martijn Peters, Greg Phillips, Giles Radford, Stefano
    Revera, Arthur Rudolph, Marko Samastur, James Salter, Jouni Sepp�nen,
    Alexander Schmolck, Tim Shirley, Geoffrey Sneddon, Ville Skytt�,
    "Vikas", Jens Svalgaard, Andy Theyers, Eric Weiser, Glyn Webster, John
    Wiseman, Paul Wright, Danny Yoo

    An incomplete list of people who made suggestions or found bugs or
    found ways to break Beautiful Soup:

     Hanno B�ck, Matteo Bertini, Chris Curvey, Simon Cusack, Bruce Eckel,
     Matt Ernst, Michael Foord, Tom Harris, Bill de hOra, Donald Howes,
     Matt Patterson, Scott Roberts, Steve Strassmann, Mike Williams,
     warchild at redho dot com, Sami Kuisma, Carlos Rocha, Bob Hutchison,
     Joren Mc, Michal Migurski, John Kleven, Tim Heaney, Tripp Lilley, Ed
     Summers, Dennis Sutch, Chris Smith, Aaron Swartz, Stuart
     Turner, Greg Edwards, Kevin J Kalupson, Nikos Kouremenos, Artur de
     Sousa Rocha, Yichun Wei, Per Vognsen

    Beautiful Soup is made available under the MIT license:

     Copyright (c) Leonard Richardson

     Permission is hereby granted, free of charge, to any person obtaining
     a copy of this software and associated documentation files (the
     "Software"), to deal in the Software without restriction, including
     without limitation the rights to use, copy, modify, merge, publish,
     distribute, sublicense, and/or sell copies of the Software, and to
     permit persons to whom the Software is furnished to do so, subject to
     the following conditions:

     The above copyright notice and this permission notice shall be
     included in all copies or substantial portions of the Software.

     THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
     EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
     MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
     NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
     BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
     ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
     CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
     SOFTWARE.

    Beautiful Soup incorporates code from the html5lib library, which is
    also made available under the MIT license. Copyright (c) James Graham
    and other contributors

    Beautiful Soup has an optional dependency on the soupsieve library,
    which is also made available under the MIT license. Copyright (c)
    Isaac Muse

---
### certifi

    This package contains a modified version of ca-bundle.crt:

    ca-bundle.crt -- Bundle of CA Root Certificates

    This is a bundle of X.509 certificates of public Certificate Authorities
    (CA). These were automatically extracted from Mozilla's root certificates
    file (certdata.txt).  This file can be found in the mozilla source tree:
    https://hg.mozilla.org/mozilla-central/file/tip/security/nss/lib/ckfw/builtins/certdata.txt
    It contains the certificates in PEM format and therefore
    can be directly used with curl / libcurl / php_curl, or with
    an Apache+mod_ssl webserver for SSL client authentication.
    Just configure this file as the SSLCACertificateFile.#

    ***** BEGIN LICENSE BLOCK *****
    This Source Code Form is subject to the terms of the Mozilla Public License,
    v. 2.0. If a copy of the MPL was not distributed with this file, You can obtain
    one at http://mozilla.org/MPL/2.0/.

    ***** END LICENSE BLOCK *****
    @(#) $RCSfile: certdata.txt,v $ $Revision: 1.80 $ $Date: 2011/11/03 15:11:58 $

---
### charset-normalizer

    MIT License

    Copyright (c) 2025 TAHRI Ahmed R.

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

---
### coverage

                                  Apache License
                            Version 2.0, January 2004
                         http://www.apache.org/licenses/

    TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

    1. Definitions.

       "License" shall mean the terms and conditions for use, reproduction,
       and distribution as defined by Sections 1 through 9 of this document.

       "Licensor" shall mean the copyright owner or entity authorized by
       the copyright owner that is granting the License.

       "Legal Entity" shall mean the union of the acting entity and all
       other entities that control, are controlled by, or are under common
       control with that entity. For the purposes of this definition,
       "control" means (i) the power, direct or indirect, to cause the
       direction or management of such entity, whether by contract or
       otherwise, or (ii) ownership of fifty percent (50%) or more of the
       outstanding shares, or (iii) beneficial ownership of such entity.

       "You" (or "Your") shall mean an individual or Legal Entity
       exercising permissions granted by this License.

       "Source" form shall mean the preferred form for making modifications,
       including but not limited to software source code, documentation
       source, and configuration files.

       "Object" form shall mean any form resulting from mechanical
       transformation or translation of a Source form, including but
       not limited to compiled object code, generated documentation,
       and conversions to other media types.

       "Work" shall mean the work of authorship, whether in Source or
       Object form, made available under the License, as indicated by a
       copyright notice that is included in or attached to the work
       (an example is provided in the Appendix below).

       "Derivative Works" shall mean any work, whether in Source or Object
       form, that is based on (or derived from) the Work and for which the
       editorial revisions, annotations, elaborations, or other modifications
       represent, as a whole, an original work of authorship. For the purposes
       of this License, Derivative Works shall not include works that remain
       separable from, or merely link (or bind by name) to the interfaces of,
       the Work and Derivative Works thereof.

       "Contribution" shall mean any work of authorship, including
       the original version of the Work and any modifications or additions
       to that Work or Derivative Works thereof, that is intentionally
       submitted to Licensor for inclusion in the Work by the copyright owner
       or by an individual or Legal Entity authorized to submit on behalf of
       the copyright owner. For the purposes of this definition, "submitted"
       means any form of electronic, verbal, or written communication sent
       to the Licensor or its representatives, including but not limited to
       communication on electronic mailing lists, source code control systems,
       and issue tracking systems that are managed by, or on behalf of, the
       Licensor for the purpose of discussing and improving the Work, but
       excluding communication that is conspicuously marked or otherwise
       designated in writing by the copyright owner as "Not a Contribution."

       "Contributor" shall mean Licensor and any individual or Legal Entity
       on behalf of whom a Contribution has been received by Licensor and
       subsequently incorporated within the Work.

    2. Grant of Copyright License. Subject to the terms and conditions of
       this License, each Contributor hereby grants to You a perpetual,
       worldwide, non-exclusive, no-charge, royalty-free, irrevocable
       copyright license to reproduce, prepare Derivative Works of,
       publicly display, publicly perform, sublicense, and distribute the
       Work and such Derivative Works in Source or Object form.

    3. Grant of Patent License. Subject to the terms and conditions of
       this License, each Contributor hereby grants to You a perpetual,
       worldwide, non-exclusive, no-charge, royalty-free, irrevocable
       (except as stated in this section) patent license to make, have made,
       use, offer to sell, sell, import, and otherwise transfer the Work,
       where such license applies only to those patent claims licensable
       by such Contributor that are necessarily infringed by their
       Contribution(s) alone or by combination of their Contribution(s)
       with the Work to which such Contribution(s) was submitted. If You
       institute patent litigation against any entity (including a
       cross-claim or counterclaim in a lawsuit) alleging that the Work
       or a Contribution incorporated within the Work constitutes direct
       or contributory patent infringement, then any patent licenses
       granted to You under this License for that Work shall terminate
       as of the date such litigation is filed.

    4. Redistribution. You may reproduce and distribute copies of the
       Work or Derivative Works thereof in any medium, with or without
       modifications, and in Source or Object form, provided that You
       meet the following conditions:

       (a) You must give any other recipients of the Work or
           Derivative Works a copy of this License; and

       (b) You must cause any modified files to carry prominent notices
           stating that You changed the files; and

       (c) You must retain, in the Source form of any Derivative Works
           that You distribute, all copyright, patent, trademark, and
           attribution notices from the Source form of the Work,
           excluding those notices that do not pertain to any part of
           the Derivative Works; and

       (d) If the Work includes a "NOTICE" text file as part of its
           distribution, then any Derivative Works that You distribute must
           include a readable copy of the attribution notices contained
           within such NOTICE file, excluding those notices that do not
           pertain to any part of the Derivative Works, in at least one
           of the following places: within a NOTICE text file distributed
           as part of the Derivative Works; within the Source form or
           documentation, if provided along with the Derivative Works; or,
           within a display generated by the Derivative Works, if and
           wherever such third-party notices normally appear. The contents
           of the NOTICE file are for informational purposes only and
           do not modify the License. You may add Your own attribution
           notices within Derivative Works that You distribute, alongside
           or as an addendum to the NOTICE text from the Work, provided
           that such additional attribution notices cannot be construed
           as modifying the License.

       You may add Your own copyright statement to Your modifications and
       may provide additional or different license terms and conditions
       for use, reproduction, or distribution of Your modifications, or
       for any such Derivative Works as a whole, provided Your use,
       reproduction, and distribution of the Work otherwise complies with
       the conditions stated in this License.

    5. Submission of Contributions. Unless You explicitly state otherwise,
       any Contribution intentionally submitted for inclusion in the Work
       by You to the Licensor shall be under the terms and conditions of
       this License, without any additional terms or conditions.
       Notwithstanding the above, nothing herein shall supersede or modify
       the terms of any separate license agreement you may have executed
       with Licensor regarding such Contributions.

    6. Trademarks. This License does not grant permission to use the trade
       names, trademarks, service marks, or product names of the Licensor,
       except as required for reasonable and customary use in describing the
       origin of the Work and reproducing the content of the NOTICE file.

    7. Disclaimer of Warranty. Unless required by applicable law or
       agreed to in writing, Licensor provides the Work (and each
       Contributor provides its Contributions) on an "AS IS" BASIS,
       WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
       implied, including, without limitation, any warranties or conditions
       of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
       PARTICULAR PURPOSE. You are solely responsible for determining the
       appropriateness of using or redistributing the Work and assume any
       risks associated with Your exercise of permissions under this License.

    8. Limitation of Liability. In no event and under no legal theory,
       whether in tort (including negligence), contract, or otherwise,
       unless required by applicable law (such as deliberate and grossly
       negligent acts) or agreed to in writing, shall any Contributor be
       liable to You for damages, including any direct, indirect, special,
       incidental, or consequential damages of any character arising as a
       result of this License or out of the use or inability to use the
       Work (including but not limited to damages for loss of goodwill,
       work stoppage, computer failure or malfunction, or any and all
       other commercial damages or losses), even if such Contributor
       has been advised of the possibility of such damages.

    9. Accepting Warranty or Additional Liability. While redistributing
       the Work or Derivative Works thereof, You may choose to offer,
       and charge a fee for, acceptance of support, warranty, indemnity,
       or other liability obligations and/or rights consistent with this
       License. However, in accepting such obligations, You may act only
       on Your own behalf and on Your sole responsibility, not on behalf
       of any other Contributor, and only if You agree to indemnify,
       defend, and hold each Contributor harmless for any liability
       incurred by, or claims asserted against, such Contributor by reason
       of your accepting any such warranty or additional liability.

    END OF TERMS AND CONDITIONS

    Copyright 2001 Gareth Rees.  All rights reserved.
    Copyright 2004-2026 Ned Batchelder.  All rights reserved.

    Except where noted otherwise, this software is licensed under the Apache
    License, Version 2.0 (the "License"); you may not use this work except in
    compliance with the License.  You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

---
### fastapi

    The MIT License (MIT)

    Copyright (c) 2018 Sebastián Ramírez

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.

---
### h11

    The MIT License (MIT)

    Copyright (c) 2016 Nathaniel J. Smith <njs@pobox.com> and other contributors

    Permission is hereby granted, free of charge, to any person obtaining
    a copy of this software and associated documentation files (the
    "Software"), to deal in the Software without restriction, including
    without limitation the rights to use, copy, modify, merge, publish,
    distribute, sublicense, and/or sell copies of the Software, and to
    permit persons to whom the Software is furnished to do so, subject to
    the following conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
    LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
    OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
    WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---
### httpcore

    Copyright © 2020, [Encode OSS Ltd](https://www.encode.io/).
    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice, this
      list of conditions and the following disclaimer.

    * Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer in the documentation
      and/or other materials provided with the distribution.

    * Neither the name of the copyright holder nor the names of its
      contributors may be used to endorse or promote products derived from
      this software without specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
    AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
    IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
    DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
    FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
    DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
    SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
    CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
    OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
    OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

---
### httpx

    Copyright © 2019, [Encode OSS Ltd](https://www.encode.io/).
    All rights reserved.

    Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

    * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

    * Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

---
### httpx_auth

    MIT License

    Copyright (c) 2024 Colin Bounouar

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

---
### idna

    BSD 3-Clause License

    Copyright (c) 2013-2026, Kim Davies and contributors.
    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are
    met:

    1. Redistributions of source code must retain the above copyright
       notice, this list of conditions and the following disclaimer.

    2. Redistributions in binary form must reproduce the above copyright
       notice, this list of conditions and the following disclaimer in the
       documentation and/or other materials provided with the distribution.

    3. Neither the name of the copyright holder nor the names of its
       contributors may be used to endorse or promote products derived from
       this software without specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
    "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
    LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
    A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
    HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
    SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
    TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
    PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
    LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
    NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
    SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

---
### iniconfig

    The MIT License (MIT)

    Copyright (c) 2010 - 2023 Holger Krekel and others

    Permission is hereby granted, free of charge, to any person obtaining a copy of
    this software and associated documentation files (the "Software"), to deal in
    the Software without restriction, including without limitation the rights to
    use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
    of the Software, and to permit persons to whom the Software is furnished to do
    so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

---
### Mako

    Copyright 2006-2026 the Mako authors and contributors <see AUTHORS file>.

    Permission is hereby granted, free of charge, to any person obtaining a copy of
    this software and associated documentation files (the "Software"), to deal in
    the Software without restriction, including without limitation the rights to
    use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
    of the Software, and to permit persons to whom the Software is furnished to do
    so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

---
### MarkupSafe

    Copyright 2010 Pallets

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are
    met:

    1.  Redistributions of source code must retain the above copyright
        notice, this list of conditions and the following disclaimer.

    2.  Redistributions in binary form must reproduce the above copyright
        notice, this list of conditions and the following disclaimer in the
        documentation and/or other materials provided with the distribution.

    3.  Neither the name of the copyright holder nor the names of its
        contributors may be used to endorse or promote products derived from
        this software without specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
    "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
    LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
    PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
    HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
    SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
    TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
    PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
    LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
    NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
    SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

---
### neo4j

                                  Apache License
                            Version 2.0, January 2004
                         https://www.apache.org/licenses/

    TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

    1. Definitions.

       "License" shall mean the terms and conditions for use, reproduction,
       and distribution as defined by Sections 1 through 9 of this document.

       "Licensor" shall mean the copyright owner or entity authorized by
       the copyright owner that is granting the License.

       "Legal Entity" shall mean the union of the acting entity and all
       other entities that control, are controlled by, or are under common
       control with that entity. For the purposes of this definition,
       "control" means (i) the power, direct or indirect, to cause the
       direction or management of such entity, whether by contract or
       otherwise, or (ii) ownership of fifty percent (50%) or more of the
       outstanding shares, or (iii) beneficial ownership of such entity.

       "You" (or "Your") shall mean an individual or Legal Entity
       exercising permissions granted by this License.

       "Source" form shall mean the preferred form for making modifications,
       including but not limited to software source code, documentation
       source, and configuration files.

       "Object" form shall mean any form resulting from mechanical
       transformation or translation of a Source form, including but
       not limited to compiled object code, generated documentation,
       and conversions to other media types.

       "Work" shall mean the work of authorship, whether in Source or
       Object form, made available under the License, as indicated by a
       copyright notice that is included in or attached to the work
       (an example is provided in the Appendix below).

       "Derivative Works" shall mean any work, whether in Source or Object
       form, that is based on (or derived from) the Work and for which the
       editorial revisions, annotations, elaborations, or other modifications
       represent, as a whole, an original work of authorship. For the purposes
       of this License, Derivative Works shall not include works that remain
       separable from, or merely link (or bind by name) to the interfaces of,
       the Work and Derivative Works thereof.

       "Contribution" shall mean any work of authorship, including
       the original version of the Work and any modifications or additions
       to that Work or Derivative Works thereof, that is intentionally
       submitted to Licensor for inclusion in the Work by the copyright owner
       or by an individual or Legal Entity authorized to submit on behalf of
       the copyright owner. For the purposes of this definition, "submitted"
       means any form of electronic, verbal, or written communication sent
       to the Licensor or its representatives, including but not limited to
       communication on electronic mailing lists, source code control systems,
       and issue tracking systems that are managed by, or on behalf of, the
       Licensor for the purpose of discussing and improving the Work, but
       excluding communication that is conspicuously marked or otherwise
       designated in writing by the copyright owner as "Not a Contribution."

       "Contributor" shall mean Licensor and any individual or Legal Entity
       on behalf of whom a Contribution has been received by Licensor and
       subsequently incorporated within the Work.

    2. Grant of Copyright License. Subject to the terms and conditions of
       this License, each Contributor hereby grants to You a perpetual,
       worldwide, non-exclusive, no-charge, royalty-free, irrevocable
       copyright license to reproduce, prepare Derivative Works of,
       publicly display, publicly perform, sublicense, and distribute the
       Work and such Derivative Works in Source or Object form.

    3. Grant of Patent License. Subject to the terms and conditions of
       this License, each Contributor hereby grants to You a perpetual,
       worldwide, non-exclusive, no-charge, royalty-free, irrevocable
       (except as stated in this section) patent license to make, have made,
       use, offer to sell, sell, import, and otherwise transfer the Work,
       where such license applies only to those patent claims licensable
       by such Contributor that are necessarily infringed by their
       Contribution(s) alone or by combination of their Contribution(s)
       with the Work to which such Contribution(s) was submitted. If You
       institute patent litigation against any entity (including a
       cross-claim or counterclaim in a lawsuit) alleging that the Work
       or a Contribution incorporated within the Work constitutes direct
       or contributory patent infringement, then any patent licenses
       granted to You under this License for that Work shall terminate
       as of the date such litigation is filed.

    4. Redistribution. You may reproduce and distribute copies of the
       Work or Derivative Works thereof in any medium, with or without
       modifications, and in Source or Object form, provided that You
       meet the following conditions:

       (a) You must give any other recipients of the Work or
           Derivative Works a copy of this License; and

       (b) You must cause any modified files to carry prominent notices
           stating that You changed the files; and

       (c) You must retain, in the Source form of any Derivative Works
           that You distribute, all copyright, patent, trademark, and
           attribution notices from the Source form of the Work,
           excluding those notices that do not pertain to any part of
           the Derivative Works; and

       (d) If the Work includes a "NOTICE" text file as part of its
           distribution, then any Derivative Works that You distribute must
           include a readable copy of the attribution notices contained
           within such NOTICE file, excluding those notices that do not
           pertain to any part of the Derivative Works, in at least one
           of the following places: within a NOTICE text file distributed
           as part of the Derivative Works; within the Source form or
           documentation, if provided along with the Derivative Works; or,
           within a display generated by the Derivative Works, if and
           wherever such third-party notices normally appear. The contents
           of the NOTICE file are for informational purposes only and
           do not modify the License. You may add Your own attribution
           notices within Derivative Works that You distribute, alongside
           or as an addendum to the NOTICE text from the Work, provided
           that such additional attribution notices cannot be construed
           as modifying the License.

       You may add Your own copyright statement to Your modifications and
       may provide additional or different license terms and conditions
       for use, reproduction, or distribution of Your modifications, or
       for any such Derivative Works as a whole, provided Your use,
       reproduction, and distribution of the Work otherwise complies with
       the conditions stated in this License.

    5. Submission of Contributions. Unless You explicitly state otherwise,
       any Contribution intentionally submitted for inclusion in the Work
       by You to the Licensor shall be under the terms and conditions of
       this License, without any additional terms or conditions.
       Notwithstanding the above, nothing herein shall supersede or modify
       the terms of any separate license agreement you may have executed
       with Licensor regarding such Contributions.

    6. Trademarks. This License does not grant permission to use the trade
       names, trademarks, service marks, or product names of the Licensor,
       except as required for reasonable and customary use in describing the
       origin of the Work and reproducing the content of the NOTICE file.

    7. Disclaimer of Warranty. Unless required by applicable law or
       agreed to in writing, Licensor provides the Work (and each
       Contributor provides its Contributions) on an "AS IS" BASIS,
       WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
       implied, including, without limitation, any warranties or conditions
       of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
       PARTICULAR PURPOSE. You are solely responsible for determining the
       appropriateness of using or redistributing the Work and assume any
       risks associated with Your exercise of permissions under this License.

    8. Limitation of Liability. In no event and under no legal theory,
       whether in tort (including negligence), contract, or otherwise,
       unless required by applicable law (such as deliberate and grossly
       negligent acts) or agreed to in writing, shall any Contributor be
       liable to You for damages, including any direct, indirect, special,
       incidental, or consequential damages of any character arising as a
       result of this License or out of the use or inability to use the
       Work (including but not limited to damages for loss of goodwill,
       work stoppage, computer failure or malfunction, or any and all
       other commercial damages or losses), even if such Contributor
       has been advised of the possibility of such damages.

    9. Accepting Warranty or Additional Liability. While redistributing
       the Work or Derivative Works thereof, You may choose to offer,
       and charge a fee for, acceptance of support, warranty, indemnity,
       or other liability obligations and/or rights consistent with this
       License. However, in accepting such obligations, You may act only
       on Your own behalf and on Your sole responsibility, not on behalf
       of any other Contributor, and only if You agree to indemnify,
       defend, and hold each Contributor harmless for any liability
       incurred by, or claims asserted against, such Contributor by reason
       of your accepting any such warranty or additional liability.

    END OF TERMS AND CONDITIONS

    APPENDIX: How to apply the Apache License to your work.

       To apply the Apache License to your work, attach the following
       boilerplate notice, with the fields enclosed by brackets "[]"
       replaced with your own identifying information. (Don't include
       the brackets!)  The text should be enclosed in the appropriate
       comment syntax for the file format. We also recommend that a
       file or class name and description of purpose be included on the
       same "printed page" as the copyright notice for easier
       identification within third-party archives.

    Copyright [yyyy] [name of copyright owner]

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        https://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

    Python software and documentation are licensed under the
    Python Software Foundation License Version 2.

    Starting with Python 3.8.6, examples, recipes, and other code in
    the documentation are dual licensed under the PSF License Version 2
    and the Zero-Clause BSD license.


    PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2
    --------------------------------------------

    1. This LICENSE AGREEMENT is between the Python Software Foundation
    ("PSF"), and the Individual or Organization ("Licensee") accessing and
    otherwise using this software ("Python") in source or binary form and
    its associated documentation.

    2. Subject to the terms and conditions of this License Agreement, PSF hereby
    grants Licensee a nonexclusive, royalty-free, world-wide license to reproduce,
    analyze, test, perform and/or display publicly, prepare derivative works,
    distribute, and otherwise use Python alone or in any derivative version,
    provided, however, that PSF's License Agreement and PSF's notice of copyright,
    i.e., "Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010,
    2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022 Python Software Foundation;
    All Rights Reserved" are retained in Python alone or in any derivative version
    prepared by Licensee.

    3. In the event Licensee prepares a derivative work that is based on
    or incorporates Python or any part thereof, and wants to make
    the derivative work available to others as provided herein, then
    Licensee hereby agrees to include in any such work a brief summary of
    the changes made to Python.

    4. PSF is making Python available to Licensee on an "AS IS"
    basis.  PSF MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR
    IMPLIED.  BY WAY OF EXAMPLE, BUT NOT LIMITATION, PSF MAKES NO AND
    DISCLAIMS ANY REPRESENTATION OR WARRANTY OF MERCHANTABILITY OR FITNESS
    FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF PYTHON WILL NOT
    INFRINGE ANY THIRD PARTY RIGHTS.

    5. PSF SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF PYTHON
    FOR ANY INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES OR LOSS AS
    A RESULT OF MODIFYING, DISTRIBUTING, OR OTHERWISE USING PYTHON,
    OR ANY DERIVATIVE THEREOF, EVEN IF ADVISED OF THE POSSIBILITY THEREOF.

    6. This License Agreement will automatically terminate upon a material
    breach of its terms and conditions.

    7. Nothing in this License Agreement shall be deemed to create any
    relationship of agency, partnership, or joint venture between PSF and
    Licensee.  This License Agreement does not grant permission to use PSF
    trademarks or trade name in a trademark sense to endorse or promote
    products or services of Licensee, or any third party.

    8. By copying, installing or otherwise using Python, Licensee
    agrees to be bound by the terms and conditions of this License
    Agreement.

    Unless stated otherwise, this software is distributed under the terms of the Apache License 2.0.
    See the LICENSE.APACHE2.txt file for the full license text.

    Parts of this software is distributed under the terms of the Python Software Foundation License Version 2.
    See the LICENSE.PYTHON.txt file for the full license text.
    The pieces of code covered by the Python Software Foundation License Version 2 are marked as such.

    Neo4j
    Copyright (c) Neo4j Sweden AB (referred to in this notice as "Neo4j") [https://neo4j.com]

    This product includes software ("Software") developed by Neo4j

---
### neomodel

    The MIT License (MIT)

    Copyright 2013 Robin Edwards and other contributors

    Permission is hereby granted, free of charge, to any person obtaining
    a copy of this software and associated documentation files (the
    "Software"), to deal in the Software without restriction, including
    without limitation the rights to use, copy, modify, merge, publish,
    distribute, sublicense, and/or sell copies of the Software, and to
    permit persons to whom the Software is furnished to do so, subject to
    the following conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
    LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
    OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
    WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    Dave Vernon - https://github.com/the4thv
    Laura Willis - https://github.com/laurawillis
    Marianna Polatoglou - https://github.com/mar-chi-pan
    Murtaza Gulamali - https://github.com/mygulamali
    Nigel Small - https://github.com/nigelsmall
    Panos Katseas - https://github.com/pkatseas
    Peter Neubauer - https://github.com/peterneubauer
    Rafael Pivato - https://github.com/rafaelpivato
    Robin Edwards - https://github.com/robinedwards
    Romain Thalineau - https://github.com/romaintha
    Sam Millar - https://github.com/millr
    Siddharth Maheshwari - https://github.com/siddharthm
    Tony Landis - https://github.com/tony-landis
    Wes Freeman - https://github.com/wfreeman
    Laurie Clark-Michalek - https://github.com/bluepeppers

---
### packaging

    This software is made available under the terms of *either* of the licenses
    found in LICENSE.APACHE or LICENSE.BSD. Contributions to this software is made
    under the terms of *both* these licenses.

                                  Apache License
                            Version 2.0, January 2004
                         http://www.apache.org/licenses/

    TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

    1. Definitions.

       "License" shall mean the terms and conditions for use, reproduction,
       and distribution as defined by Sections 1 through 9 of this document.

       "Licensor" shall mean the copyright owner or entity authorized by
       the copyright owner that is granting the License.

       "Legal Entity" shall mean the union of the acting entity and all
       other entities that control, are controlled by, or are under common
       control with that entity. For the purposes of this definition,
       "control" means (i) the power, direct or indirect, to cause the
       direction or management of such entity, whether by contract or
       otherwise, or (ii) ownership of fifty percent (50%) or more of the
       outstanding shares, or (iii) beneficial ownership of such entity.

       "You" (or "Your") shall mean an individual or Legal Entity
       exercising permissions granted by this License.

       "Source" form shall mean the preferred form for making modifications,
       including but not limited to software source code, documentation
       source, and configuration files.

       "Object" form shall mean any form resulting from mechanical
       transformation or translation of a Source form, including but
       not limited to compiled object code, generated documentation,
       and conversions to other media types.

       "Work" shall mean the work of authorship, whether in Source or
       Object form, made available under the License, as indicated by a
       copyright notice that is included in or attached to the work
       (an example is provided in the Appendix below).

       "Derivative Works" shall mean any work, whether in Source or Object
       form, that is based on (or derived from) the Work and for which the
       editorial revisions, annotations, elaborations, or other modifications
       represent, as a whole, an original work of authorship. For the purposes
       of this License, Derivative Works shall not include works that remain
       separable from, or merely link (or bind by name) to the interfaces of,
       the Work and Derivative Works thereof.

       "Contribution" shall mean any work of authorship, including
       the original version of the Work and any modifications or additions
       to that Work or Derivative Works thereof, that is intentionally
       submitted to Licensor for inclusion in the Work by the copyright owner
       or by an individual or Legal Entity authorized to submit on behalf of
       the copyright owner. For the purposes of this definition, "submitted"
       means any form of electronic, verbal, or written communication sent
       to the Licensor or its representatives, including but not limited to
       communication on electronic mailing lists, source code control systems,
       and issue tracking systems that are managed by, or on behalf of, the
       Licensor for the purpose of discussing and improving the Work, but
       excluding communication that is conspicuously marked or otherwise
       designated in writing by the copyright owner as "Not a Contribution."

       "Contributor" shall mean Licensor and any individual or Legal Entity
       on behalf of whom a Contribution has been received by Licensor and
       subsequently incorporated within the Work.

    2. Grant of Copyright License. Subject to the terms and conditions of
       this License, each Contributor hereby grants to You a perpetual,
       worldwide, non-exclusive, no-charge, royalty-free, irrevocable
       copyright license to reproduce, prepare Derivative Works of,
       publicly display, publicly perform, sublicense, and distribute the
       Work and such Derivative Works in Source or Object form.

    3. Grant of Patent License. Subject to the terms and conditions of
       this License, each Contributor hereby grants to You a perpetual,
       worldwide, non-exclusive, no-charge, royalty-free, irrevocable
       (except as stated in this section) patent license to make, have made,
       use, offer to sell, sell, import, and otherwise transfer the Work,
       where such license applies only to those patent claims licensable
       by such Contributor that are necessarily infringed by their
       Contribution(s) alone or by combination of their Contribution(s)
       with the Work to which such Contribution(s) was submitted. If You
       institute patent litigation against any entity (including a
       cross-claim or counterclaim in a lawsuit) alleging that the Work
       or a Contribution incorporated within the Work constitutes direct
       or contributory patent infringement, then any patent licenses
       granted to You under this License for that Work shall terminate
       as of the date such litigation is filed.

    4. Redistribution. You may reproduce and distribute copies of the
       Work or Derivative Works thereof in any medium, with or without
       modifications, and in Source or Object form, provided that You
       meet the following conditions:

       (a) You must give any other recipients of the Work or
           Derivative Works a copy of this License; and

       (b) You must cause any modified files to carry prominent notices
           stating that You changed the files; and

       (c) You must retain, in the Source form of any Derivative Works
           that You distribute, all copyright, patent, trademark, and
           attribution notices from the Source form of the Work,
           excluding those notices that do not pertain to any part of
           the Derivative Works; and

       (d) If the Work includes a "NOTICE" text file as part of its
           distribution, then any Derivative Works that You distribute must
           include a readable copy of the attribution notices contained
           within such NOTICE file, excluding those notices that do not
           pertain to any part of the Derivative Works, in at least one
           of the following places: within a NOTICE text file distributed
           as part of the Derivative Works; within the Source form or
           documentation, if provided along with the Derivative Works; or,
           within a display generated by the Derivative Works, if and
           wherever such third-party notices normally appear. The contents
           of the NOTICE file are for informational purposes only and
           do not modify the License. You may add Your own attribution
           notices within Derivative Works that You distribute, alongside
           or as an addendum to the NOTICE text from the Work, provided
           that such additional attribution notices cannot be construed
           as modifying the License.

       You may add Your own copyright statement to Your modifications and
       may provide additional or different license terms and conditions
       for use, reproduction, or distribution of Your modifications, or
       for any such Derivative Works as a whole, provided Your use,
       reproduction, and distribution of the Work otherwise complies with
       the conditions stated in this License.

    5. Submission of Contributions. Unless You explicitly state otherwise,
       any Contribution intentionally submitted for inclusion in the Work
       by You to the Licensor shall be under the terms and conditions of
       this License, without any additional terms or conditions.
       Notwithstanding the above, nothing herein shall supersede or modify
       the terms of any separate license agreement you may have executed
       with Licensor regarding such Contributions.

    6. Trademarks. This License does not grant permission to use the trade
       names, trademarks, service marks, or product names of the Licensor,
       except as required for reasonable and customary use in describing the
       origin of the Work and reproducing the content of the NOTICE file.

    7. Disclaimer of Warranty. Unless required by applicable law or
       agreed to in writing, Licensor provides the Work (and each
       Contributor provides its Contributions) on an "AS IS" BASIS,
       WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
       implied, including, without limitation, any warranties or conditions
       of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
       PARTICULAR PURPOSE. You are solely responsible for determining the
       appropriateness of using or redistributing the Work and assume any
       risks associated with Your exercise of permissions under this License.

    8. Limitation of Liability. In no event and under no legal theory,
       whether in tort (including negligence), contract, or otherwise,
       unless required by applicable law (such as deliberate and grossly
       negligent acts) or agreed to in writing, shall any Contributor be
       liable to You for damages, including any direct, indirect, special,
       incidental, or consequential damages of any character arising as a
       result of this License or out of the use or inability to use the
       Work (including but not limited to damages for loss of goodwill,
       work stoppage, computer failure or malfunction, or any and all
       other commercial damages or losses), even if such Contributor
       has been advised of the possibility of such damages.

    9. Accepting Warranty or Additional Liability. While redistributing
       the Work or Derivative Works thereof, You may choose to offer,
       and charge a fee for, acceptance of support, warranty, indemnity,
       or other liability obligations and/or rights consistent with this
       License. However, in accepting such obligations, You may act only
       on Your own behalf and on Your sole responsibility, not on behalf
       of any other Contributor, and only if You agree to indemnify,
       defend, and hold each Contributor harmless for any liability
       incurred by, or claims asserted against, such Contributor by reason
       of your accepting any such warranty or additional liability.

    END OF TERMS AND CONDITIONS

    Copyright (c) Donald Stufft and individual contributors.
    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are met:

        1. Redistributions of source code must retain the above copyright notice,
           this list of conditions and the following disclaimer.

        2. Redistributions in binary form must reproduce the above copyright
           notice, this list of conditions and the following disclaimer in the
           documentation and/or other materials provided with the distribution.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
    ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
    WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
    DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
    FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
    DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
    SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
    CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
    OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
    OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

---
### pluggy

    The MIT License (MIT)

    Copyright (c) 2015 holger krekel (rather uses bitbucket/hpk42)

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

---
### pydantic

    The MIT License (MIT)

    Copyright (c) 2017 to present Pydantic Services Inc. and individual contributors.

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

---
### pydantic_core

    The MIT License (MIT)

    Copyright (c) 2022 Samuel Colvin

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

---
### Pygments

    Pygments is written and maintained by Georg Brandl <georg@python.org>.

    Major developers are Tim Hatch <tim@timhatch.com> and Armin Ronacher
    <armin.ronacher@active-4.com>.

    Other contributors, listed alphabetically, are:

    * Sam Aaron -- Ioke lexer
    * Jean Abou Samra -- LilyPond lexer
    * João Abecasis -- JSLT lexer
    * Ali Afshar -- image formatter
    * Thomas Aglassinger -- Easytrieve, JCL, Rexx, Transact-SQL and VBScript
      lexers
    * Maxence Ahlouche -- PostgreSQL Explain lexer
    * Muthiah Annamalai -- Ezhil lexer
    * Nikolay Antipov -- OpenSCAD lexer
    * Kumar Appaiah -- Debian control lexer
    * Andreas Amann -- AppleScript lexer
    * Timothy Armstrong -- Dart lexer fixes
    * Jeffrey Arnold -- R/S, Rd, BUGS, Jags, and Stan lexers
    * Eiríkr Åsheim -- Uxntal lexer
    * Jeremy Ashkenas -- CoffeeScript lexer
    * José Joaquín Atria -- Praat lexer
    * Stefan Matthias Aust -- Smalltalk lexer
    * Lucas Bajolet -- Nit lexer
    * Ben Bangert -- Mako lexers
    * Max Battcher -- Darcs patch lexer
    * Thomas Baruchel -- APL lexer
    * Tim Baumann -- (Literate) Agda lexer
    * Paul Baumgart, 280 North, Inc. -- Objective-J lexer
    * Michael Bayer -- Myghty lexers
    * Thomas Beale -- Archetype lexers
    * John Benediktsson -- Factor lexer
    * David Benjamin, Google LLC -- TLS lexer
    * Trevor Bergeron -- mIRC formatter
    * Vincent Bernat -- LessCSS lexer
    * Christopher Bertels -- Fancy lexer
    * Sébastien Bigaret -- QVT Operational lexer
    * Jarrett Billingsley -- MiniD lexer
    * Adam Blinkinsop -- Haskell, Redcode lexers
    * Stéphane Blondon -- Procfile, SGF and Sieve lexers
    * Frits van Bommel -- assembler lexers
    * Pierre Bourdon -- bugfixes
    * Martijn Braam -- Kernel log lexer, BARE lexer
    * JD Browne, Google LLC -- GoogleSQL lexer
    * Matthias Bussonnier -- ANSI style handling for terminal-256 formatter
    * chebee7i -- Python traceback lexer improvements
    * Hiram Chirino -- Scaml and Jade lexers
    * Mauricio Caceres -- SAS and Stata lexers.
    * Michael Camilleri, John Gabriele, sogaiu -- Janet lexer
    * Daren Chandisingh -- Gleam lexer
    * Ian Cooper -- VGL lexer
    * David Corbett -- Inform, Jasmin, JSGF, Snowball, and TADS 3 lexers
    * Leaf Corcoran -- MoonScript lexer
    * Fraser Cormack -- TableGen lexer
    * Gabriel Corona -- ASN.1 lexer
    * Radu Costache -- Boogie and Civl Verifier lexer improvements
    * Christopher Creutzig -- MuPAD lexer
    * Daniël W. Crompton -- Pike lexer
    * Pete Curry -- bugfixes
    * Bryan Davis -- EBNF lexer
    * Bruno Deferrari -- Shen lexer
    * Walter Dörwald -- UL4 lexer
    * Luke Drummond -- Meson lexer
    * Giedrius Dubinskas -- HTML formatter improvements
    * Owen Durni -- Haxe lexer
    * Alexander Dutton, Oxford University Computing Services -- SPARQL lexer
    * James Edwards -- Terraform lexer
    * Nick Efford -- Python 3 lexer
    * Sven Efftinge -- Xtend lexer
    * Artem Egorkine -- terminal256 formatter
    * Matthew Fernandez -- CAmkES lexer
    * Paweł Fertyk -- GDScript lexer, HTML formatter improvements
    * Michael Ficarra -- CPSA lexer
    * James H. Fisher -- PostScript lexer
    * Amanda Fitch, Google LLC -- GoogleSQL lexer
    * William S. Fulton -- SWIG lexer
    * Carlos Galdino -- Elixir and Elixir Console lexers
    * Michael Galloy -- IDL lexer
    * Naveen Garg -- Autohotkey lexer
    * Simon Garnotel -- FreeFem++ lexer
    * Laurent Gautier -- R/S lexer
    * Alex Gaynor -- PyPy log lexer
    * Richard Gerkin -- Igor Pro lexer
    * Alain Gilbert -- TypeScript lexer
    * Alex Gilding -- BlitzBasic lexer
    * GitHub, Inc -- DASM16, Augeas, TOML, and Slash lexers
    * Bertrand Goetzmann -- Groovy lexer
    * Krzysiek Goj -- Scala lexer
    * Rostyslav Golda -- FloScript lexer
    * Andrey Golovizin -- BibTeX lexers
    * Matt Good -- Genshi, Cheetah lexers
    * Michał Górny -- vim modeline support
    * Alex Gosse -- TrafficScript lexer
    * Patrick Gotthardt -- PHP namespaces support
    * Hubert Gruniaux -- C and C++ lexer improvements
    * Olivier Guibe -- Asymptote lexer
    * Armin Günther -- Go lexer improvements
    * Phil Hagelberg -- Fennel lexer
    * Florian Hahn -- Boogie lexer
    * Martin Harriman -- SNOBOL lexer
    * Matthew Harrison -- SVG formatter
    * Steven Hazel -- Tcl lexer
    * Dan Michael Heggø -- Turtle lexer
    * Aslak Hellesøy -- Gherkin lexer
    * Greg Hendershott -- Racket lexer
    * Justin Hendrick -- ParaSail lexer
    * Jordi Gutiérrez Hermoso -- Octave lexer
    * David Hess, Fish Software, Inc. -- Objective-J lexer
    * Ken Hilton -- Typographic Number Theory and Arrow lexers
    * Varun Hiremath -- Debian control lexer
    * Rob Hoelz -- Perl 6 lexer
    * Doug Hogan -- Mscgen lexer
    * Ben Hollis -- Mason lexer
    * Max Horn -- GAP lexer
    * Fred Hornsey -- OMG IDL Lexer
    * Alastair Houghton -- Lexer inheritance facility
    * Tim Howard -- BlitzMax lexer
    * Dustin Howett -- Logos lexer
    * Ivan Inozemtsev -- Fantom lexer
    * Hiroaki Itoh -- Shell console rewrite, Lexers for PowerShell session,
      MSDOS session, BC, WDiff
    * Brian R. Jackson -- Tea lexer
    * Alex Jeffery, ChromaWay AB -- Rell lexer
    * Christian Jann -- ShellSession lexer
    * Jonas Camillus Jeppesen -- Line numbers and line highlighting for 
      RTF-formatter
    * Dennis Kaarsemaker -- sources.list lexer
    * Dmitri Kabak -- Inferno Limbo lexer
    * Igor Kalnitsky -- vhdl lexer
    * Colin Kennedy - USD lexer
    * Alexander Kit -- MaskJS lexer
    * Pekka Klärck -- Robot Framework lexer
    * Gerwin Klein -- Isabelle lexer
    * Eric Knibbe -- Lasso lexer
    * Stepan Koltsov -- Clay lexer
    * Oliver Kopp - Friendly grayscale style
    * Adam Koprowski -- Opa lexer
    * Benjamin Kowarsch -- Modula-2 lexer
    * Domen Kožar -- Nix lexer
    * Oleh Krekel -- Emacs Lisp lexer
    * Alexander Kriegisch -- Kconfig and AspectJ lexers
    * Marek Kubica -- Scheme lexer
    * Jochen Kupperschmidt -- Markdown processor
    * Gerd Kurzbach -- Modelica lexer
    * Jon Larimer, Google Inc. -- Smali lexer
    * Olov Lassus -- Dart lexer
    * Matt Layman -- TAP lexer
    * Dan Lazin, Google LLC -- GoogleSQL lexer
    * Kristian Lyngstøl -- Varnish lexers
    * Sylvestre Ledru -- Scilab lexer
    * Chee Sing Lee -- Flatline lexer
    * Mark Lee -- Vala lexer
    * Thomas Linder Puls -- Visual Prolog lexer
    * Pete Lomax -- Phix lexer
    * Valentin Lorentz -- C++ lexer improvements
    * Ben Mabey -- Gherkin lexer
    * Angus MacArthur -- QML lexer
    * Louis Mandel -- X10 lexer
    * Louis Marchand -- Eiffel lexer
    * Simone Margaritelli -- Hybris lexer
    * Tim Martin - World of Warcraft TOC lexer
    * Kirk McDonald -- D lexer
    * Gordon McGregor -- SystemVerilog lexer
    * Stephen McKamey -- Duel/JBST lexer
    * Brian McKenna -- F# lexer
    * Charles McLaughlin -- Puppet lexer
    * Kurt McKee -- Tera Term macro lexer, PostgreSQL updates, MySQL overhaul, JSON lexer
    * Joe Eli McIlvain -- Savi lexer
    * Lukas Meuser -- BBCode formatter, Lua lexer
    * Bruno Mesquita -- Night Owl style
    * Cat Miller -- Pig lexer
    * Paul Miller -- LiveScript lexer
    * Hong Minhee -- HTTP lexer
    * Michael Mior -- Awk lexer
    * Bruce Mitchener -- Dylan lexer rewrite
    * Reuben Morais -- SourcePawn lexer
    * Jon Morton -- Rust lexer
    * Paulo Moura -- Logtalk lexer
    * Mher Movsisyan -- DTD lexer
    * Dejan Muhamedagic -- Crmsh lexer
    * Adrien Nayrat -- PostgreSQL Explain lexer
    * Ana Nelson -- Ragel, ANTLR, R console lexers
    * David Neto, Google LLC -- WebGPU Shading Language lexer
    * Kurt Neufeld -- Markdown lexer
    * Nam T. Nguyen -- Monokai style
    * Jesper Noehr -- HTML formatter "anchorlinenos"
    * Mike Nolta -- Julia lexer
    * Avery Nortonsmith -- Pointless lexer
    * Jonas Obrist -- BBCode lexer
    * Edward O'Callaghan -- Cryptol lexer
    * David Oliva -- Rebol lexer
    * Pat Pannuto -- nesC lexer
    * Jon Parise -- Protocol buffers and Thrift lexers
    * Benjamin Peterson -- Test suite refactoring
    * Ronny Pfannschmidt -- BBCode lexer
    * Dominik Picheta -- Nimrod lexer
    * Andrew Pinkham -- RTF Formatter Refactoring
    * Clément Prévost -- UrbiScript lexer
    * Tanner Prynn -- cmdline -x option and loading lexers from files
    * Oleh Prypin -- Crystal lexer (based on Ruby lexer)
    * Nick Psaris -- K and Q lexers
    * Xidorn Quan -- Web IDL lexer
    * Elias Rabel -- Fortran fixed form lexer
    * raichoo -- Idris lexer
    * Daniel Ramirez -- GDScript lexer
    * Kashif Rasul -- CUDA lexer
    * Nathan Reed -- HLSL lexer
    * Justin Reidy -- MXML lexer
    * Jonathon Reinhart, Google LLC -- Soong lexer
    * Norman Richards -- JSON lexer
    * Corey Richardson -- Rust lexer updates
    * Fabrizio Riguzzi -- cplint leder
    * Lubomir Rintel -- GoodData MAQL and CL lexers
    * Andre Roberge -- Tango style
    * Georg Rollinger -- HSAIL lexer
    * Michiel Roos -- TypoScript lexer
    * Konrad Rudolph -- LaTeX formatter enhancements
    * Mario Ruggier -- Evoque lexers
    * Miikka Salminen -- Lovelace style, Hexdump lexer, lexer enhancements
    * Stou Sandalski -- NumPy, FORTRAN, tcsh and XSLT lexers
    * Matteo Sasso -- Common Lisp lexer
    * Joe Schafer -- Ada lexer
    * Max Schillinger -- TiddlyWiki5 lexer
    * Andrew Schmidt -- X++ lexer
    * Ken Schutte -- Matlab lexers
    * René Schwaiger -- Rainbow Dash style
    * Sebastian Schweizer -- Whiley lexer
    * Tassilo Schweyer -- Io, MOOCode lexers
    * Pablo Seminario -- PromQL lexer
    * Ted Shaw -- AutoIt lexer
    * Joerg Sieker -- ABAP lexer
    * Robert Simmons -- Standard ML lexer
    * Kirill Simonov -- YAML lexer
    * Corbin Simpson -- Monte lexer
    * Ville Skyttä -- ASCII armored lexer
    * Alexander Smishlajev -- Visual FoxPro lexer
    * Steve Spigarelli -- XQuery lexer
    * Jerome St-Louis -- eC lexer
    * Camil Staps -- Clean and NuSMV lexers; Solarized style
    * James Strachan -- Kotlin lexer
    * Tom Stuart -- Treetop lexer
    * Colin Sullivan -- SuperCollider lexer
    * Ben Swift -- Extempore lexer
    * tatt61880 -- Kuin lexer
    * Edoardo Tenani -- Arduino lexer
    * Tiberius Teng -- default style overhaul
    * Jeremy Thurgood -- Erlang, Squid config lexers
    * Brian Tiffin -- OpenCOBOL lexer
    * Bob Tolbert -- Hy lexer
    * Doug Torrance -- Macaulay2 lexer
    * Matthias Trute -- Forth lexer
    * Tuoa Spi T4 -- Bdd lexer
    * Erick Tryzelaar -- Felix lexer
    * Alexander Udalov -- Kotlin lexer improvements
    * Thomas Van Doren -- Chapel lexer
    * Dave Van Ee -- Uxntal lexer updates
    * Daniele Varrazzo -- PostgreSQL lexers
    * Abe Voelker -- OpenEdge ABL lexer
    * Pepijn de Vos -- HTML formatter CTags support
    * Matthias Vallentin -- Bro lexer
    * Benoît Vinot -- AMPL lexer
    * Linh Vu Hong -- RSL lexer
    * Taavi Väänänen -- Debian control, PHP lexers
    * Immanuel Washington -- Smithy lexer
    * Nathan Weizenbaum -- Haml and Sass lexers
    * Nathan Whetsell -- Csound lexers
    * Dietmar Winkler -- Modelica lexer
    * Nils Winter -- Smalltalk lexer
    * Trevor Woerner -- BitBake lexer
    * Davy Wybiral -- Clojure lexer
    * Whitney Young -- ObjectiveC lexer
    * Diego Zamboni -- CFengine3 lexer
    * Enrique Zamudio -- Ceylon lexer
    * Alex Zimin -- Nemerle lexer
    * Rob Zimmerman -- Kal lexer
    * Evgenii Zheltonozhskii -- Maple lexer
    * Vincent Zurczak -- Roboconf lexer
    * Hubert Gruniaux -- C and C++ lexer improvements
    * Thomas Symalla -- AMDGPU Lexer
    * 15b3 -- Image Formatter improvements
    * Fabian Neumann -- CDDL lexer
    * Thomas Duboucher -- CDDL lexer
    * Philipp Imhof -- Pango Markup formatter
    * Thomas Voss -- Sed lexer
    * Martin Fischer -- WCAG contrast testing
    * Marc Auberer -- Spice lexer
    * Amr Hesham -- Carbon lexer
    * diskdance -- Wikitext lexer
    * vanillajonathan -- PRQL lexer
    * Nikolay Antipov -- OpenSCAD lexer
    * Markus Meyer, Nextron Systems -- YARA lexer
    * Hannes Römer -- Mojo lexer
    * Jan Frederik Schaefer -- PDDL lexer

    Many thanks for all contributions!

    Copyright (c) 2006-2022 by the respective authors (see AUTHORS file).
    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are
    met:

    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.

    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
    "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
    LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
    A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
    OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
    SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
    LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
    DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
    THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
    (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
    OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

---
### pytest

    The MIT License (MIT)

    Copyright (c) 2004 Holger Krekel and others

    Permission is hereby granted, free of charge, to any person obtaining a copy of
    this software and associated documentation files (the "Software"), to deal in
    the Software without restriction, including without limitation the rights to
    use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
    of the Software, and to permit persons to whom the Software is furnished to do
    so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

---
### pytest-cov

    Authors
    =======

    * Marc Schlaich - https://github.com/schlamar (\http://www.schlamar.org)
    * Rick van Hattem - http://wol.ph
    * Buck Evan - https://github.com/bukzor
    * Eric Larson - http://larsoner.com
    * Marc Abramowitz - \http://marc-abramowitz.com
    * Thomas Kluyver - https://github.com/takluyver
    * Guillaume Ayoub - http://www.yabz.fr
    * Federico Ceratto - \http://firelet.net
    * Josh Kalderimis - \http://blog.cookiestack.com
    * Ionel Cristian Mărieș - https://blog.ionelmc.ro
    * Christian Ledermann - https://github.com/cleder
    * Alec Nikolas Reiter - https://github.com/justanr
    * Patrick Lannigan - https://github.com/plannigan
    * David Szotten - https://github.com/davidszotten
    * Michael Elovskikh - https://github.com/wronglink
    * Saurabh Kumar - https://github.com/theskumar
    * Michael Elovskikh - https://github.com/wronglink
    * Daniel Hahler - https://github.com/blueyed (\https://daniel.hahler.de)
    * Florian Bruhin - http://www.the-compiler.org
    * Zoltan Kozma - https://github.com/kozmaz87
    * Francis Niu - https://flniu.github.io
    * Jannis Leidel - https://github.com/jezdez
    * Ryan Hiebert - http://ryanhiebert.com/
    * Terence Honles - https://github.com/terencehonles
    * Jeremy Bowman - https://github.com/jmbowman
    * Samuel Giffard - https://github.com/Mulugruntz
    * Семён Марьясин - https://github.com/MarSoft
    * Alexander Shadchin - https://github.com/shadchin
    * Thomas Grainger - https://graingert.co.uk
    * Juanjo Bazán - https://github.com/xuanxu
    * Andrew Murray - https://github.com/radarhere
    * Ned Batchelder - https://nedbatchelder.com/
    * Albert Tugushev - https://github.com/atugushev
    * Martín Gaitán - https://github.com/mgaitan
    * Hugo van Kemenade - https://github.com/hugovk
    * Michael Manganiello - https://github.com/adamantike
    * Anders Hovmöller - https://github.com/boxed
    * Zac Hatfield-Dodds - https://zhd.dev
    * Mateus Berardo de Souza Terra - https://github.com/MatTerra
    * Ganden Schaffner - https://github.com/gschaffner
    * Michał Górny - https://github.com/mgorny
    * Bernát Gábor - https://github.com/gaborbernat
    * Pamela McA'Nulty - https://github.com/PamelaM
    * Christian Riedel - https://github.com/Cielquan
    * Chris Sreesangkom - https://github.com/csreesan
    * Sorin Sbarnea - https://github.com/ssbarnea
    * Brian Rutledge - https://github.com/bhrutledge
    * Danilo Šegan - https://github.com/dsegan
    * Michał Bielawski - https://github.com/D3X
    * Zac Hatfield-Dodds - https://github.com/Zac-HD
    * Ben Greiner - https://github.com/bnavigator
    * Delgan - https://github.com/Delgan
    * Andre Brisco - https://github.com/abrisco
    * Colin O'Dell - https://github.com/colinodell
    * Ronny Pfannschmidt - https://github.com/RonnyPfannschmidt
    * Christian Fetzer - https://github.com/fetzerch
    * Jonathan Stewmon - https://github.com/jstewmon
    * Matthew Gamble - https://github.com/mwgamble
    * Christian Clauss - https://github.com/cclauss
    * Dawn James - https://github.com/dawngerpony
    * Tsvika Shapira - https://github.com/tsvikas
    * Marcos Boger - https://github.com/marcosboger
    * Ofek Lev - https://github.com/ofek

    The MIT License

    Copyright (c) 2010 Meme Dough

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.

---
### pytz

    Copyright (c) 2003-2019 Stuart Bishop <stuart@stuartbishop.net>

    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the "Software"),
    to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    DEALINGS IN THE SOFTWARE.

---
### requests

                                  Apache License
                            Version 2.0, January 2004
                         http://www.apache.org/licenses/

    TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

    1. Definitions.

       "License" shall mean the terms and conditions for use, reproduction,
       and distribution as defined by Sections 1 through 9 of this document.

       "Licensor" shall mean the copyright owner or entity authorized by
       the copyright owner that is granting the License.

       "Legal Entity" shall mean the union of the acting entity and all
       other entities that control, are controlled by, or are under common
       control with that entity. For the purposes of this definition,
       "control" means (i) the power, direct or indirect, to cause the
       direction or management of such entity, whether by contract or
       otherwise, or (ii) ownership of fifty percent (50%) or more of the
       outstanding shares, or (iii) beneficial ownership of such entity.

       "You" (or "Your") shall mean an individual or Legal Entity
       exercising permissions granted by this License.

       "Source" form shall mean the preferred form for making modifications,
       including but not limited to software source code, documentation
       source, and configuration files.

       "Object" form shall mean any form resulting from mechanical
       transformation or translation of a Source form, including but
       not limited to compiled object code, generated documentation,
       and conversions to other media types.

       "Work" shall mean the work of authorship, whether in Source or
       Object form, made available under the License, as indicated by a
       copyright notice that is included in or attached to the work
       (an example is provided in the Appendix below).

       "Derivative Works" shall mean any work, whether in Source or Object
       form, that is based on (or derived from) the Work and for which the
       editorial revisions, annotations, elaborations, or other modifications
       represent, as a whole, an original work of authorship. For the purposes
       of this License, Derivative Works shall not include works that remain
       separable from, or merely link (or bind by name) to the interfaces of,
       the Work and Derivative Works thereof.

       "Contribution" shall mean any work of authorship, including
       the original version of the Work and any modifications or additions
       to that Work or Derivative Works thereof, that is intentionally
       submitted to Licensor for inclusion in the Work by the copyright owner
       or by an individual or Legal Entity authorized to submit on behalf of
       the copyright owner. For the purposes of this definition, "submitted"
       means any form of electronic, verbal, or written communication sent
       to the Licensor or its representatives, including but not limited to
       communication on electronic mailing lists, source code control systems,
       and issue tracking systems that are managed by, or on behalf of, the
       Licensor for the purpose of discussing and improving the Work, but
       excluding communication that is conspicuously marked or otherwise
       designated in writing by the copyright owner as "Not a Contribution."

       "Contributor" shall mean Licensor and any individual or Legal Entity
       on behalf of whom a Contribution has been received by Licensor and
       subsequently incorporated within the Work.

    2. Grant of Copyright License. Subject to the terms and conditions of
       this License, each Contributor hereby grants to You a perpetual,
       worldwide, non-exclusive, no-charge, royalty-free, irrevocable
       copyright license to reproduce, prepare Derivative Works of,
       publicly display, publicly perform, sublicense, and distribute the
       Work and such Derivative Works in Source or Object form.

    3. Grant of Patent License. Subject to the terms and conditions of
       this License, each Contributor hereby grants to You a perpetual,
       worldwide, non-exclusive, no-charge, royalty-free, irrevocable
       (except as stated in this section) patent license to make, have made,
       use, offer to sell, sell, import, and otherwise transfer the Work,
       where such license applies only to those patent claims licensable
       by such Contributor that are necessarily infringed by their
       Contribution(s) alone or by combination of their Contribution(s)
       with the Work to which such Contribution(s) was submitted. If You
       institute patent litigation against any entity (including a
       cross-claim or counterclaim in a lawsuit) alleging that the Work
       or a Contribution incorporated within the Work constitutes direct
       or contributory patent infringement, then any patent licenses
       granted to You under this License for that Work shall terminate
       as of the date such litigation is filed.

    4. Redistribution. You may reproduce and distribute copies of the
       Work or Derivative Works thereof in any medium, with or without
       modifications, and in Source or Object form, provided that You
       meet the following conditions:

       (a) You must give any other recipients of the Work or
           Derivative Works a copy of this License; and

       (b) You must cause any modified files to carry prominent notices
           stating that You changed the files; and

       (c) You must retain, in the Source form of any Derivative Works
           that You distribute, all copyright, patent, trademark, and
           attribution notices from the Source form of the Work,
           excluding those notices that do not pertain to any part of
           the Derivative Works; and

       (d) If the Work includes a "NOTICE" text file as part of its
           distribution, then any Derivative Works that You distribute must
           include a readable copy of the attribution notices contained
           within such NOTICE file, excluding those notices that do not
           pertain to any part of the Derivative Works, in at least one
           of the following places: within a NOTICE text file distributed
           as part of the Derivative Works; within the Source form or
           documentation, if provided along with the Derivative Works; or,
           within a display generated by the Derivative Works, if and
           wherever such third-party notices normally appear. The contents
           of the NOTICE file are for informational purposes only and
           do not modify the License. You may add Your own attribution
           notices within Derivative Works that You distribute, alongside
           or as an addendum to the NOTICE text from the Work, provided
           that such additional attribution notices cannot be construed
           as modifying the License.

       You may add Your own copyright statement to Your modifications and
       may provide additional or different license terms and conditions
       for use, reproduction, or distribution of Your modifications, or
       for any such Derivative Works as a whole, provided Your use,
       reproduction, and distribution of the Work otherwise complies with
       the conditions stated in this License.

    5. Submission of Contributions. Unless You explicitly state otherwise,
       any Contribution intentionally submitted for inclusion in the Work
       by You to the Licensor shall be under the terms and conditions of
       this License, without any additional terms or conditions.
       Notwithstanding the above, nothing herein shall supersede or modify
       the terms of any separate license agreement you may have executed
       with Licensor regarding such Contributions.

    6. Trademarks. This License does not grant permission to use the trade
       names, trademarks, service marks, or product names of the Licensor,
       except as required for reasonable and customary use in describing the
       origin of the Work and reproducing the content of the NOTICE file.

    7. Disclaimer of Warranty. Unless required by applicable law or
       agreed to in writing, Licensor provides the Work (and each
       Contributor provides its Contributions) on an "AS IS" BASIS,
       WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
       implied, including, without limitation, any warranties or conditions
       of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
       PARTICULAR PURPOSE. You are solely responsible for determining the
       appropriateness of using or redistributing the Work and assume any
       risks associated with Your exercise of permissions under this License.

    8. Limitation of Liability. In no event and under no legal theory,
       whether in tort (including negligence), contract, or otherwise,
       unless required by applicable law (such as deliberate and grossly
       negligent acts) or agreed to in writing, shall any Contributor be
       liable to You for damages, including any direct, indirect, special,
       incidental, or consequential damages of any character arising as a
       result of this License or out of the use or inability to use the
       Work (including but not limited to damages for loss of goodwill,
       work stoppage, computer failure or malfunction, or any and all
       other commercial damages or losses), even if such Contributor
       has been advised of the possibility of such damages.

    9. Accepting Warranty or Additional Liability. While redistributing
       the Work or Derivative Works thereof, You may choose to offer,
       and charge a fee for, acceptance of support, warranty, indemnity,
       or other liability obligations and/or rights consistent with this
       License. However, in accepting such obligations, You may act only
       on Your own behalf and on Your sole responsibility, not on behalf
       of any other Contributor, and only if You agree to indemnify,
       defend, and hold each Contributor harmless for any liability
       incurred by, or claims asserted against, such Contributor by reason
       of your accepting any such warranty or additional liability.

    Requests
    Copyright 2019 Kenneth Reitz

---
### soupsieve

    MIT License

    Copyright (c) 2018 - 2026 Isaac Muse <isaacmuse@gmail.com>

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

---
### starlette

    Copyright © 2018, [Encode OSS Ltd](https://www.encode.io/).
    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice, this
      list of conditions and the following disclaimer.

    * Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer in the documentation
      and/or other materials provided with the distribution.

    * Neither the name of the copyright holder nor the names of its
      contributors may be used to endorse or promote products derived from
      this software without specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
    AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
    IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
    DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
    FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
    DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
    SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
    CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
    OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
    OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

---
### typing_extensions

    A. HISTORY OF THE SOFTWARE
    ==========================

    Python was created in the early 1990s by Guido van Rossum at Stichting
    Mathematisch Centrum (CWI, see https://www.cwi.nl) in the Netherlands
    as a successor of a language called ABC.  Guido remains Python's
    principal author, although it includes many contributions from others.

    In 1995, Guido continued his work on Python at the Corporation for
    National Research Initiatives (CNRI, see https://www.cnri.reston.va.us)
    in Reston, Virginia where he released several versions of the
    software.

    In May 2000, Guido and the Python core development team moved to
    BeOpen.com to form the BeOpen PythonLabs team.  In October of the same
    year, the PythonLabs team moved to Digital Creations, which became
    Zope Corporation.  In 2001, the Python Software Foundation (PSF, see
    https://www.python.org/psf/) was formed, a non-profit organization
    created specifically to own Python-related Intellectual Property.
    Zope Corporation was a sponsoring member of the PSF.

    All Python releases are Open Source (see https://opensource.org for
    the Open Source Definition).  Historically, most, but not all, Python
    releases have also been GPL-compatible; the table below summarizes
    the various releases.

        Release         Derived     Year        Owner       GPL-
                        from                                compatible? (1)

        0.9.0 thru 1.2              1991-1995   CWI         yes
        1.3 thru 1.5.2  1.2         1995-1999   CNRI        yes
        1.6             1.5.2       2000        CNRI        no
        2.0             1.6         2000        BeOpen.com  no
        1.6.1           1.6         2001        CNRI        yes (2)
        2.1             2.0+1.6.1   2001        PSF         no
        2.0.1           2.0+1.6.1   2001        PSF         yes
        2.1.1           2.1+2.0.1   2001        PSF         yes
        2.1.2           2.1.1       2002        PSF         yes
        2.1.3           2.1.2       2002        PSF         yes
        2.2 and above   2.1.1       2001-now    PSF         yes

    Footnotes:

    (1) GPL-compatible doesn't mean that we're distributing Python under
        the GPL.  All Python licenses, unlike the GPL, let you distribute
        a modified version without making your changes open source.  The
        GPL-compatible licenses make it possible to combine Python with
        other software that is released under the GPL; the others don't.

    (2) According to Richard Stallman, 1.6.1 is not GPL-compatible,
        because its license has a choice of law clause.  According to
        CNRI, however, Stallman's lawyer has told CNRI's lawyer that 1.6.1
        is "not incompatible" with the GPL.

    Thanks to the many outside volunteers who have worked under Guido's
    direction to make these releases possible.


    B. TERMS AND CONDITIONS FOR ACCESSING OR OTHERWISE USING PYTHON
    ===============================================================

    Python software and documentation are licensed under the
    Python Software Foundation License Version 2.

    Starting with Python 3.8.6, examples, recipes, and other code in
    the documentation are dual licensed under the PSF License Version 2
    and the Zero-Clause BSD license.

    Some software incorporated into Python is under different licenses.
    The licenses are listed with code falling under that license.


    PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2
    --------------------------------------------

    1. This LICENSE AGREEMENT is between the Python Software Foundation
    ("PSF"), and the Individual or Organization ("Licensee") accessing and
    otherwise using this software ("Python") in source or binary form and
    its associated documentation.

    2. Subject to the terms and conditions of this License Agreement, PSF hereby
    grants Licensee a nonexclusive, royalty-free, world-wide license to reproduce,
    analyze, test, perform and/or display publicly, prepare derivative works,
    distribute, and otherwise use Python alone or in any derivative version,
    provided, however, that PSF's License Agreement and PSF's notice of copyright,
    i.e., "Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010,
    2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023 Python Software Foundation;
    All Rights Reserved" are retained in Python alone or in any derivative version
    prepared by Licensee.

    3. In the event Licensee prepares a derivative work that is based on
    or incorporates Python or any part thereof, and wants to make
    the derivative work available to others as provided herein, then
    Licensee hereby agrees to include in any such work a brief summary of
    the changes made to Python.

    4. PSF is making Python available to Licensee on an "AS IS"
    basis.  PSF MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR
    IMPLIED.  BY WAY OF EXAMPLE, BUT NOT LIMITATION, PSF MAKES NO AND
    DISCLAIMS ANY REPRESENTATION OR WARRANTY OF MERCHANTABILITY OR FITNESS
    FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF PYTHON WILL NOT
    INFRINGE ANY THIRD PARTY RIGHTS.

    5. PSF SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF PYTHON
    FOR ANY INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES OR LOSS AS
    A RESULT OF MODIFYING, DISTRIBUTING, OR OTHERWISE USING PYTHON,
    OR ANY DERIVATIVE THEREOF, EVEN IF ADVISED OF THE POSSIBILITY THEREOF.

    6. This License Agreement will automatically terminate upon a material
    breach of its terms and conditions.

    7. Nothing in this License Agreement shall be deemed to create any
    relationship of agency, partnership, or joint venture between PSF and
    Licensee.  This License Agreement does not grant permission to use PSF
    trademarks or trade name in a trademark sense to endorse or promote
    products or services of Licensee, or any third party.

    8. By copying, installing or otherwise using Python, Licensee
    agrees to be bound by the terms and conditions of this License
    Agreement.


    BEOPEN.COM LICENSE AGREEMENT FOR PYTHON 2.0
    -------------------------------------------

    BEOPEN PYTHON OPEN SOURCE LICENSE AGREEMENT VERSION 1

    1. This LICENSE AGREEMENT is between BeOpen.com ("BeOpen"), having an
    office at 160 Saratoga Avenue, Santa Clara, CA 95051, and the
    Individual or Organization ("Licensee") accessing and otherwise using
    this software in source or binary form and its associated
    documentation ("the Software").

    2. Subject to the terms and conditions of this BeOpen Python License
    Agreement, BeOpen hereby grants Licensee a non-exclusive,
    royalty-free, world-wide license to reproduce, analyze, test, perform
    and/or display publicly, prepare derivative works, distribute, and
    otherwise use the Software alone or in any derivative version,
    provided, however, that the BeOpen Python License is retained in the
    Software, alone or in any derivative version prepared by Licensee.

    3. BeOpen is making the Software available to Licensee on an "AS IS"
    basis.  BEOPEN MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR
    IMPLIED.  BY WAY OF EXAMPLE, BUT NOT LIMITATION, BEOPEN MAKES NO AND
    DISCLAIMS ANY REPRESENTATION OR WARRANTY OF MERCHANTABILITY OR FITNESS
    FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF THE SOFTWARE WILL NOT
    INFRINGE ANY THIRD PARTY RIGHTS.

    4. BEOPEN SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF THE
    SOFTWARE FOR ANY INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES OR LOSS
    AS A RESULT OF USING, MODIFYING OR DISTRIBUTING THE SOFTWARE, OR ANY
    DERIVATIVE THEREOF, EVEN IF ADVISED OF THE POSSIBILITY THEREOF.

    5. This License Agreement will automatically terminate upon a material
    breach of its terms and conditions.

    6. This License Agreement shall be governed by and interpreted in all
    respects by the law of the State of California, excluding conflict of
    law provisions.  Nothing in this License Agreement shall be deemed to
    create any relationship of agency, partnership, or joint venture
    between BeOpen and Licensee.  This License Agreement does not grant
    permission to use BeOpen trademarks or trade names in a trademark
    sense to endorse or promote products or services of Licensee, or any
    third party.  As an exception, the "BeOpen Python" logos available at
    http://www.pythonlabs.com/logos.html may be used according to the
    permissions granted on that web page.

    7. By copying, installing or otherwise using the software, Licensee
    agrees to be bound by the terms and conditions of this License
    Agreement.


    CNRI LICENSE AGREEMENT FOR PYTHON 1.6.1
    ---------------------------------------

    1. This LICENSE AGREEMENT is between the Corporation for National
    Research Initiatives, having an office at 1895 Preston White Drive,
    Reston, VA 20191 ("CNRI"), and the Individual or Organization
    ("Licensee") accessing and otherwise using Python 1.6.1 software in
    source or binary form and its associated documentation.

    2. Subject to the terms and conditions of this License Agreement, CNRI
    hereby grants Licensee a nonexclusive, royalty-free, world-wide
    license to reproduce, analyze, test, perform and/or display publicly,
    prepare derivative works, distribute, and otherwise use Python 1.6.1
    alone or in any derivative version, provided, however, that CNRI's
    License Agreement and CNRI's notice of copyright, i.e., "Copyright (c)
    1995-2001 Corporation for National Research Initiatives; All Rights
    Reserved" are retained in Python 1.6.1 alone or in any derivative
    version prepared by Licensee.  Alternately, in lieu of CNRI's License
    Agreement, Licensee may substitute the following text (omitting the
    quotes): "Python 1.6.1 is made available subject to the terms and
    conditions in CNRI's License Agreement.  This Agreement together with
    Python 1.6.1 may be located on the internet using the following
    unique, persistent identifier (known as a handle): 1895.22/1013.  This
    Agreement may also be obtained from a proxy server on the internet
    using the following URL: http://hdl.handle.net/1895.22/1013".

    3. In the event Licensee prepares a derivative work that is based on
    or incorporates Python 1.6.1 or any part thereof, and wants to make
    the derivative work available to others as provided herein, then
    Licensee hereby agrees to include in any such work a brief summary of
    the changes made to Python 1.6.1.

    4. CNRI is making Python 1.6.1 available to Licensee on an "AS IS"
    basis.  CNRI MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR
    IMPLIED.  BY WAY OF EXAMPLE, BUT NOT LIMITATION, CNRI MAKES NO AND
    DISCLAIMS ANY REPRESENTATION OR WARRANTY OF MERCHANTABILITY OR FITNESS
    FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF PYTHON 1.6.1 WILL NOT
    INFRINGE ANY THIRD PARTY RIGHTS.

    5. CNRI SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF PYTHON
    1.6.1 FOR ANY INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES OR LOSS AS
    A RESULT OF MODIFYING, DISTRIBUTING, OR OTHERWISE USING PYTHON 1.6.1,
    OR ANY DERIVATIVE THEREOF, EVEN IF ADVISED OF THE POSSIBILITY THEREOF.

    6. This License Agreement will automatically terminate upon a material
    breach of its terms and conditions.

    7. This License Agreement shall be governed by the federal
    intellectual property law of the United States, including without
    limitation the federal copyright law, and, to the extent such
    U.S. federal law does not apply, by the law of the Commonwealth of
    Virginia, excluding Virginia's conflict of law provisions.
    Notwithstanding the foregoing, with regard to derivative works based
    on Python 1.6.1 that incorporate non-separable material that was
    previously distributed under the GNU General Public License (GPL), the
    law of the Commonwealth of Virginia shall govern this License
    Agreement only as to issues arising under or with respect to
    Paragraphs 4, 5, and 7 of this License Agreement.  Nothing in this
    License Agreement shall be deemed to create any relationship of
    agency, partnership, or joint venture between CNRI and Licensee.  This
    License Agreement does not grant permission to use CNRI trademarks or
    trade name in a trademark sense to endorse or promote products or
    services of Licensee, or any third party.

    8. By clicking on the "ACCEPT" button where indicated, or by copying,
    installing or otherwise using Python 1.6.1, Licensee agrees to be
    bound by the terms and conditions of this License Agreement.

            ACCEPT


    CWI LICENSE AGREEMENT FOR PYTHON 0.9.0 THROUGH 1.2
    --------------------------------------------------

    Copyright (c) 1991 - 1995, Stichting Mathematisch Centrum Amsterdam,
    The Netherlands.  All rights reserved.

    Permission to use, copy, modify, and distribute this software and its
    documentation for any purpose and without fee is hereby granted,
    provided that the above copyright notice appear in all copies and that
    both that copyright notice and this permission notice appear in
    supporting documentation, and that the name of Stichting Mathematisch
    Centrum or CWI not be used in advertising or publicity pertaining to
    distribution of the software without specific, written prior
    permission.

    STICHTING MATHEMATISCH CENTRUM DISCLAIMS ALL WARRANTIES WITH REGARD TO
    THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
    FITNESS, IN NO EVENT SHALL STICHTING MATHEMATISCH CENTRUM BE LIABLE
    FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
    WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
    ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
    OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

    ZERO-CLAUSE BSD LICENSE FOR CODE IN THE PYTHON DOCUMENTATION
    ----------------------------------------------------------------------

    Permission to use, copy, modify, and/or distribute this software for any
    purpose with or without fee is hereby granted.

    THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
    REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
    AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
    INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
    LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
    OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
    PERFORMANCE OF THIS SOFTWARE.

---
### typing-inspection

    MIT License

    Copyright (c) Pydantic Services Inc. 2025 to present

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

---
### urllib3

    MIT License

    Copyright (c) 2008-2020 Andrey Petrov and contributors.

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

