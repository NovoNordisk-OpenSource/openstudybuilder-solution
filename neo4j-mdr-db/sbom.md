
## Installed packages

|            Package             |       Version        |
|--------------------------------|----------------------|
| certifi                        | 2024.8.30            |
| charset-normalizer             | 3.4.0                |
| idna                           | 3.10                 |
| neo4j                          | 4.4.12               |
| pip                            | 25.0.1               |
| pytz                           | 2024.2               |
| requests                       | 2.32.3               |
| urllib3                        | 2.2.3                |


## Third-party package licenses


---

### License for 3rd party library certifi

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

### License for 3rd party library charset-normalizer

MIT License

Copyright (c) 2019 TAHRI Ahmed R.

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

### License for 3rd party library idna

BSD 3-Clause License

Copyright (c) 2013-2024, Kim Davies and contributors.
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

### License for 3rd party library neo4j

Neo4j
Copyright (c) Neo4j Sweden AB (referred to in this notice as "Neo4j") [http://neo4j.com]

This product includes software ("Software") developed by Neo4j

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

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.


---

### License for 3rd party library pip

#######################################################################################
#
# Adapted from:
#  https://github.com/pypa/hatch/blob/5352e44/backend/src/hatchling/licenses/parse.py
#
# MIT License
#
# Copyright (c) 2017-present Ofek Lev <oss@ofek.dev>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be included in all copies
# or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
# CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#
# With additional allowance of arbitrary `LicenseRef-` identifiers, not just
# `LicenseRef-Public-Domain` and `LicenseRef-Proprietary`.
#
#######################################################################################
from __future__ import annotations

import re
from typing import NewType, cast

from pip._vendor.packaging.licenses._spdx import EXCEPTIONS, LICENSES

__all__ = [
    "NormalizedLicenseExpression",
    "InvalidLicenseExpression",
    "canonicalize_license_expression",
]

license_ref_allowed = re.compile("^[A-Za-z0-9.-]*$")

NormalizedLicenseExpression = NewType("NormalizedLicenseExpression", str)


class InvalidLicenseExpression(ValueError):
    """Raised when a license-expression string is invalid

    >>> canonicalize_license_expression("invalid")
    Traceback (most recent call last):
        ...
    packaging.licenses.InvalidLicenseExpression: Invalid license expression: 'invalid'
    """


def canonicalize_license_expression(
    raw_license_expression: str,
) -> NormalizedLicenseExpression:
    if not raw_license_expression:
        message = f"Invalid license expression: {raw_license_expression!r}"
        raise InvalidLicenseExpression(message)

    # Pad any parentheses so tokenization can be achieved by merely splitting on
    # whitespace.
    license_expression = raw_license_expression.replace("(", " ( ").replace(")", " ) ")
    licenseref_prefix = "LicenseRef-"
    license_refs = {
        ref.lower(): "LicenseRef-" + ref[len(licenseref_prefix) :]
        for ref in license_expression.split()
        if ref.lower().startswith(licenseref_prefix.lower())
    }

    # Normalize to lower case so we can look up licenses/exceptions
    # and so boolean operators are Python-compatible.
    license_expression = license_expression.lower()

    tokens = license_expression.split()

    # Rather than implementing boolean logic, we create an expression that Python can
    # parse. Everything that is not involved with the grammar itself is treated as
    # `False` and the expression should evaluate as such.
    python_tokens = []
    for token in tokens:
        if token not in {"or", "and", "with", "(", ")"}:
            python_tokens.append("False")
        elif token == "with":
            python_tokens.append("or")
        elif token == "(" and python_tokens and python_tokens[-1] not in {"or", "and"}:
            message = f"Invalid license expression: {raw_license_expression!r}"
            raise InvalidLicenseExpression(message)
        else:
            python_tokens.append(token)

    python_expression = " ".join(python_tokens)
    try:
        invalid = eval(python_expression, globals(), locals())
    except Exception:
        invalid = True

    if invalid is not False:
        message = f"Invalid license expression: {raw_license_expression!r}"
        raise InvalidLicenseExpression(message) from None

    # Take a final pass to check for unknown licenses/exceptions.
    normalized_tokens = []
    for token in tokens:
        if token in {"or", "and", "with", "(", ")"}:
            normalized_tokens.append(token.upper())
            continue

        if normalized_tokens and normalized_tokens[-1] == "WITH":
            if token not in EXCEPTIONS:
                message = f"Unknown license exception: {token!r}"
                raise InvalidLicenseExpression(message)

            normalized_tokens.append(EXCEPTIONS[token]["id"])
        else:
            if token.endswith("+"):
                final_token = token[:-1]
                suffix = "+"
            else:
                final_token = token
                suffix = ""

            if final_token.startswith("licenseref-"):
                if not license_ref_allowed.match(final_token):
                    message = f"Invalid licenseref: {final_token!r}"
                    raise InvalidLicenseExpression(message)
                normalized_tokens.append(license_refs[final_token] + suffix)
            else:
                if final_token not in LICENSES:
                    message = f"Unknown license: {final_token!r}"
                    raise InvalidLicenseExpression(message)
                normalized_tokens.append(LICENSES[final_token]["id"] + suffix)

    normalized_expression = " ".join(normalized_tokens)

    return cast(
        NormalizedLicenseExpression,
        normalized_expression.replace("( ", "(").replace(" )", ")"),
    )

from __future__ import annotations

from typing import TypedDict

class SPDXLicense(TypedDict):
    id: str
    deprecated: bool

class SPDXException(TypedDict):
    id: str
    deprecated: bool


VERSION = '3.25.0'

LICENSES: dict[str, SPDXLicense] = {
    '0bsd': {'id': '0BSD', 'deprecated': False},
    '3d-slicer-1.0': {'id': '3D-Slicer-1.0', 'deprecated': False},
    'aal': {'id': 'AAL', 'deprecated': False},
    'abstyles': {'id': 'Abstyles', 'deprecated': False},
    'adacore-doc': {'id': 'AdaCore-doc', 'deprecated': False},
    'adobe-2006': {'id': 'Adobe-2006', 'deprecated': False},
    'adobe-display-postscript': {'id': 'Adobe-Display-PostScript', 'deprecated': False},
    'adobe-glyph': {'id': 'Adobe-Glyph', 'deprecated': False},
    'adobe-utopia': {'id': 'Adobe-Utopia', 'deprecated': False},
    'adsl': {'id': 'ADSL', 'deprecated': False},
    'afl-1.1': {'id': 'AFL-1.1', 'deprecated': False},
    'afl-1.2': {'id': 'AFL-1.2', 'deprecated': False},
    'afl-2.0': {'id': 'AFL-2.0', 'deprecated': False},
    'afl-2.1': {'id': 'AFL-2.1', 'deprecated': False},
    'afl-3.0': {'id': 'AFL-3.0', 'deprecated': False},
    'afmparse': {'id': 'Afmparse', 'deprecated': False},
    'agpl-1.0': {'id': 'AGPL-1.0', 'deprecated': True},
    'agpl-1.0-only': {'id': 'AGPL-1.0-only', 'deprecated': False},
    'agpl-1.0-or-later': {'id': 'AGPL-1.0-or-later', 'deprecated': False},
    'agpl-3.0': {'id': 'AGPL-3.0', 'deprecated': True},
    'agpl-3.0-only': {'id': 'AGPL-3.0-only', 'deprecated': False},
    'agpl-3.0-or-later': {'id': 'AGPL-3.0-or-later', 'deprecated': False},
    'aladdin': {'id': 'Aladdin', 'deprecated': False},
    'amd-newlib': {'id': 'AMD-newlib', 'deprecated': False},
    'amdplpa': {'id': 'AMDPLPA', 'deprecated': False},
    'aml': {'id': 'AML', 'deprecated': False},
    'aml-glslang': {'id': 'AML-glslang', 'deprecated': False},
    'ampas': {'id': 'AMPAS', 'deprecated': False},
    'antlr-pd': {'id': 'ANTLR-PD', 'deprecated': False},
    'antlr-pd-fallback': {'id': 'ANTLR-PD-fallback', 'deprecated': False},
    'any-osi': {'id': 'any-OSI', 'deprecated': False},
    'apache-1.0': {'id': 'Apache-1.0', 'deprecated': False},
    'apache-1.1': {'id': 'Apache-1.1', 'deprecated': False},
    'apache-2.0': {'id': 'Apache-2.0', 'deprecated': False},
    'apafml': {'id': 'APAFML', 'deprecated': False},
    'apl-1.0': {'id': 'APL-1.0', 'deprecated': False},
    'app-s2p': {'id': 'App-s2p', 'deprecated': False},
    'apsl-1.0': {'id': 'APSL-1.0', 'deprecated': False},
    'apsl-1.1': {'id': 'APSL-1.1', 'deprecated': False},
    'apsl-1.2': {'id': 'APSL-1.2', 'deprecated': False},
    'apsl-2.0': {'id': 'APSL-2.0', 'deprecated': False},
    'arphic-1999': {'id': 'Arphic-1999', 'deprecated': False},
    'artistic-1.0': {'id': 'Artistic-1.0', 'deprecated': False},
    'artistic-1.0-cl8': {'id': 'Artistic-1.0-cl8', 'deprecated': False},
    'artistic-1.0-perl': {'id': 'Artistic-1.0-Perl', 'deprecated': False},
    'artistic-2.0': {'id': 'Artistic-2.0', 'deprecated': False},
    'aswf-digital-assets-1.0': {'id': 'ASWF-Digital-Assets-1.0', 'deprecated': False},
    'aswf-digital-assets-1.1': {'id': 'ASWF-Digital-Assets-1.1', 'deprecated': False},
    'baekmuk': {'id': 'Baekmuk', 'deprecated': False},
    'bahyph': {'id': 'Bahyph', 'deprecated': False},
    'barr': {'id': 'Barr', 'deprecated': False},
    'bcrypt-solar-designer': {'id': 'bcrypt-Solar-Designer', 'deprecated': False},
    'beerware': {'id': 'Beerware', 'deprecated': False},
    'bitstream-charter': {'id': 'Bitstream-Charter', 'deprecated': False},
    'bitstream-vera': {'id': 'Bitstream-Vera', 'deprecated': False},
    'bittorrent-1.0': {'id': 'BitTorrent-1.0', 'deprecated': False},
    'bittorrent-1.1': {'id': 'BitTorrent-1.1', 'deprecated': False},
    'blessing': {'id': 'blessing', 'deprecated': False},
    'blueoak-1.0.0': {'id': 'BlueOak-1.0.0', 'deprecated': False},
    'boehm-gc': {'id': 'Boehm-GC', 'deprecated': False},
    'borceux': {'id': 'Borceux', 'deprecated': False},
    'brian-gladman-2-clause': {'id': 'Brian-Gladman-2-Clause', 'deprecated': False},
    'brian-gladman-3-clause': {'id': 'Brian-Gladman-3-Clause', 'deprecated': False},
    'bsd-1-clause': {'id': 'BSD-1-Clause', 'deprecated': False},
    'bsd-2-clause': {'id': 'BSD-2-Clause', 'deprecated': False},
    'bsd-2-clause-darwin': {'id': 'BSD-2-Clause-Darwin', 'deprecated': False},
    'bsd-2-clause-first-lines': {'id': 'BSD-2-Clause-first-lines', 'deprecated': False},
    'bsd-2-clause-freebsd': {'id': 'BSD-2-Clause-FreeBSD', 'deprecated': True},
    'bsd-2-clause-netbsd': {'id': 'BSD-2-Clause-NetBSD', 'deprecated': True},
    'bsd-2-clause-patent': {'id': 'BSD-2-Clause-Patent', 'deprecated': False},
    'bsd-2-clause-views': {'id': 'BSD-2-Clause-Views', 'deprecated': False},
    'bsd-3-clause': {'id': 'BSD-3-Clause', 'deprecated': False},
    'bsd-3-clause-acpica': {'id': 'BSD-3-Clause-acpica', 'deprecated': False},
    'bsd-3-clause-attribution': {'id': 'BSD-3-Clause-Attribution', 'deprecated': False},
    'bsd-3-clause-clear': {'id': 'BSD-3-Clause-Clear', 'deprecated': False},
    'bsd-3-clause-flex': {'id': 'BSD-3-Clause-flex', 'deprecated': False},
    'bsd-3-clause-hp': {'id': 'BSD-3-Clause-HP', 'deprecated': False},
    'bsd-3-clause-lbnl': {'id': 'BSD-3-Clause-LBNL', 'deprecated': False},
    'bsd-3-clause-modification': {'id': 'BSD-3-Clause-Modification', 'deprecated': False},
    'bsd-3-clause-no-military-license': {'id': 'BSD-3-Clause-No-Military-License', 'deprecated': False},
    'bsd-3-clause-no-nuclear-license': {'id': 'BSD-3-Clause-No-Nuclear-License', 'deprecated': False},
    'bsd-3-clause-no-nuclear-license-2014': {'id': 'BSD-3-Clause-No-Nuclear-License-2014', 'deprecated': False},
    'bsd-3-clause-no-nuclear-warranty': {'id': 'BSD-3-Clause-No-Nuclear-Warranty', 'deprecated': False},
    'bsd-3-clause-open-mpi': {'id': 'BSD-3-Clause-Open-MPI', 'deprecated': False},
    'bsd-3-clause-sun': {'id': 'BSD-3-Clause-Sun', 'deprecated': False},
    'bsd-4-clause': {'id': 'BSD-4-Clause', 'deprecated': False},
    'bsd-4-clause-shortened': {'id': 'BSD-4-Clause-Shortened', 'deprecated': False},
    'bsd-4-clause-uc': {'id': 'BSD-4-Clause-UC', 'deprecated': False},
    'bsd-4.3reno': {'id': 'BSD-4.3RENO', 'deprecated': False},
    'bsd-4.3tahoe': {'id': 'BSD-4.3TAHOE', 'deprecated': False},
    'bsd-advertising-acknowledgement': {'id': 'BSD-Advertising-Acknowledgement', 'deprecated': False},
    'bsd-attribution-hpnd-disclaimer': {'id': 'BSD-Attribution-HPND-disclaimer', 'deprecated': False},
    'bsd-inferno-nettverk': {'id': 'BSD-Inferno-Nettverk', 'deprecated': False},
    'bsd-protection': {'id': 'BSD-Protection', 'deprecated': False},
    'bsd-source-beginning-file': {'id': 'BSD-Source-beginning-file', 'deprecated': False},
    'bsd-source-code': {'id': 'BSD-Source-Code', 'deprecated': False},
    'bsd-systemics': {'id': 'BSD-Systemics', 'deprecated': False},
    'bsd-systemics-w3works': {'id': 'BSD-Systemics-W3Works', 'deprecated': False},
    'bsl-1.0': {'id': 'BSL-1.0', 'deprecated': False},
    'busl-1.1': {'id': 'BUSL-1.1', 'deprecated': False},
    'bzip2-1.0.5': {'id': 'bzip2-1.0.5', 'deprecated': True},
    'bzip2-1.0.6': {'id': 'bzip2-1.0.6', 'deprecated': False},
    'c-uda-1.0': {'id': 'C-UDA-1.0', 'deprecated': False},
    'cal-1.0': {'id': 'CAL-1.0', 'deprecated': False},
    'cal-1.0-combined-work-exception': {'id': 'CAL-1.0-Combined-Work-Exception', 'deprecated': False},
    'caldera': {'id': 'Caldera', 'deprecated': False},
    'caldera-no-preamble': {'id': 'Caldera-no-preamble', 'deprecated': False},
    'catharon': {'id': 'Catharon', 'deprecated': False},
    'catosl-1.1': {'id': 'CATOSL-1.1', 'deprecated': False},
    'cc-by-1.0': {'id': 'CC-BY-1.0', 'deprecated': False},
    'cc-by-2.0': {'id': 'CC-BY-2.0', 'deprecated': False},
    'cc-by-2.5': {'id': 'CC-BY-2.5', 'deprecated': False},
    'cc-by-2.5-au': {'id': 'CC-BY-2.5-AU', 'deprecated': False},
    'cc-by-3.0': {'id': 'CC-BY-3.0', 'deprecated': False},
    'cc-by-3.0-at': {'id': 'CC-BY-3.0-AT', 'deprecated': False},
    'cc-by-3.0-au': {'id': 'CC-BY-3.0-AU', 'deprecated': False},
    'cc-by-3.0-de': {'id': 'CC-BY-3.0-DE', 'deprecated': False},
    'cc-by-3.0-igo': {'id': 'CC-BY-3.0-IGO', 'deprecated': False},
    'cc-by-3.0-nl': {'id': 'CC-BY-3.0-NL', 'deprecated': False},
    'cc-by-3.0-us': {'id': 'CC-BY-3.0-US', 'deprecated': False},
    'cc-by-4.0': {'id': 'CC-BY-4.0', 'deprecated': False},
    'cc-by-nc-1.0': {'id': 'CC-BY-NC-1.0', 'deprecated': False},
    'cc-by-nc-2.0': {'id': 'CC-BY-NC-2.0', 'deprecated': False},
    'cc-by-nc-2.5': {'id': 'CC-BY-NC-2.5', 'deprecated': False},
    'cc-by-nc-3.0': {'id': 'CC-BY-NC-3.0', 'deprecated': False},
    'cc-by-nc-3.0-de': {'id': 'CC-BY-NC-3.0-DE', 'deprecated': False},
    'cc-by-nc-4.0': {'id': 'CC-BY-NC-4.0', 'deprecated': False},
    'cc-by-nc-nd-1.0': {'id': 'CC-BY-NC-ND-1.0', 'deprecated': False},
    'cc-by-nc-nd-2.0': {'id': 'CC-BY-NC-ND-2.0', 'deprecated': False},
    'cc-by-nc-nd-2.5': {'id': 'CC-BY-NC-ND-2.5', 'deprecated': False},
    'cc-by-nc-nd-3.0': {'id': 'CC-BY-NC-ND-3.0', 'deprecated': False},
    'cc-by-nc-nd-3.0-de': {'id': 'CC-BY-NC-ND-3.0-DE', 'deprecated': False},
    'cc-by-nc-nd-3.0-igo': {'id': 'CC-BY-NC-ND-3.0-IGO', 'deprecated': False},
    'cc-by-nc-nd-4.0': {'id': 'CC-BY-NC-ND-4.0', 'deprecated': False},
    'cc-by-nc-sa-1.0': {'id': 'CC-BY-NC-SA-1.0', 'deprecated': False},
    'cc-by-nc-sa-2.0': {'id': 'CC-BY-NC-SA-2.0', 'deprecated': False},
    'cc-by-nc-sa-2.0-de': {'id': 'CC-BY-NC-SA-2.0-DE', 'deprecated': False},
    'cc-by-nc-sa-2.0-fr': {'id': 'CC-BY-NC-SA-2.0-FR', 'deprecated': False},
    'cc-by-nc-sa-2.0-uk': {'id': 'CC-BY-NC-SA-2.0-UK', 'deprecated': False},
    'cc-by-nc-sa-2.5': {'id': 'CC-BY-NC-SA-2.5', 'deprecated': False},
    'cc-by-nc-sa-3.0': {'id': 'CC-BY-NC-SA-3.0', 'deprecated': False},
    'cc-by-nc-sa-3.0-de': {'id': 'CC-BY-NC-SA-3.0-DE', 'deprecated': False},
    'cc-by-nc-sa-3.0-igo': {'id': 'CC-BY-NC-SA-3.0-IGO', 'deprecated': False},
    'cc-by-nc-sa-4.0': {'id': 'CC-BY-NC-SA-4.0', 'deprecated': False},
    'cc-by-nd-1.0': {'id': 'CC-BY-ND-1.0', 'deprecated': False},
    'cc-by-nd-2.0': {'id': 'CC-BY-ND-2.0', 'deprecated': False},
    'cc-by-nd-2.5': {'id': 'CC-BY-ND-2.5', 'deprecated': False},
    'cc-by-nd-3.0': {'id': 'CC-BY-ND-3.0', 'deprecated': False},
    'cc-by-nd-3.0-de': {'id': 'CC-BY-ND-3.0-DE', 'deprecated': False},
    'cc-by-nd-4.0': {'id': 'CC-BY-ND-4.0', 'deprecated': False},
    'cc-by-sa-1.0': {'id': 'CC-BY-SA-1.0', 'deprecated': False},
    'cc-by-sa-2.0': {'id': 'CC-BY-SA-2.0', 'deprecated': False},
    'cc-by-sa-2.0-uk': {'id': 'CC-BY-SA-2.0-UK', 'deprecated': False},
    'cc-by-sa-2.1-jp': {'id': 'CC-BY-SA-2.1-JP', 'deprecated': False},
    'cc-by-sa-2.5': {'id': 'CC-BY-SA-2.5', 'deprecated': False},
    'cc-by-sa-3.0': {'id': 'CC-BY-SA-3.0', 'deprecated': False},
    'cc-by-sa-3.0-at': {'id': 'CC-BY-SA-3.0-AT', 'deprecated': False},
    'cc-by-sa-3.0-de': {'id': 'CC-BY-SA-3.0-DE', 'deprecated': False},
    'cc-by-sa-3.0-igo': {'id': 'CC-BY-SA-3.0-IGO', 'deprecated': False},
    'cc-by-sa-4.0': {'id': 'CC-BY-SA-4.0', 'deprecated': False},
    'cc-pddc': {'id': 'CC-PDDC', 'deprecated': False},
    'cc0-1.0': {'id': 'CC0-1.0', 'deprecated': False},
    'cddl-1.0': {'id': 'CDDL-1.0', 'deprecated': False},
    'cddl-1.1': {'id': 'CDDL-1.1', 'deprecated': False},
    'cdl-1.0': {'id': 'CDL-1.0', 'deprecated': False},
    'cdla-permissive-1.0': {'id': 'CDLA-Permissive-1.0', 'deprecated': False},
    'cdla-permissive-2.0': {'id': 'CDLA-Permissive-2.0', 'deprecated': False},
    'cdla-sharing-1.0': {'id': 'CDLA-Sharing-1.0', 'deprecated': False},
    'cecill-1.0': {'id': 'CECILL-1.0', 'deprecated': False},
    'cecill-1.1': {'id': 'CECILL-1.1', 'deprecated': False},
    'cecill-2.0': {'id': 'CECILL-2.0', 'deprecated': False},
    'cecill-2.1': {'id': 'CECILL-2.1', 'deprecated': False},
    'cecill-b': {'id': 'CECILL-B', 'deprecated': False},
    'cecill-c': {'id': 'CECILL-C', 'deprecated': False},
    'cern-ohl-1.1': {'id': 'CERN-OHL-1.1', 'deprecated': False},
    'cern-ohl-1.2': {'id': 'CERN-OHL-1.2', 'deprecated': False},
    'cern-ohl-p-2.0': {'id': 'CERN-OHL-P-2.0', 'deprecated': False},
    'cern-ohl-s-2.0': {'id': 'CERN-OHL-S-2.0', 'deprecated': False},
    'cern-ohl-w-2.0': {'id': 'CERN-OHL-W-2.0', 'deprecated': False},
    'cfitsio': {'id': 'CFITSIO', 'deprecated': False},
    'check-cvs': {'id': 'check-cvs', 'deprecated': False},
    'checkmk': {'id': 'checkmk', 'deprecated': False},
    'clartistic': {'id': 'ClArtistic', 'deprecated': False},
    'clips': {'id': 'Clips', 'deprecated': False},
    'cmu-mach': {'id': 'CMU-Mach', 'deprecated': False},
    'cmu-mach-nodoc': {'id': 'CMU-Mach-nodoc', 'deprecated': False},
    'cnri-jython': {'id': 'CNRI-Jython', 'deprecated': False},
    'cnri-python': {'id': 'CNRI-Python', 'deprecated': False},
    'cnri-python-gpl-compatible': {'id': 'CNRI-Python-GPL-Compatible', 'deprecated': False},
    'coil-1.0': {'id': 'COIL-1.0', 'deprecated': False},
    'community-spec-1.0': {'id': 'Community-Spec-1.0', 'deprecated': False},
    'condor-1.1': {'id': 'Condor-1.1', 'deprecated': False},
    'copyleft-next-0.3.0': {'id': 'copyleft-next-0.3.0', 'deprecated': False},
    'copyleft-next-0.3.1': {'id': 'copyleft-next-0.3.1', 'deprecated': False},
    'cornell-lossless-jpeg': {'id': 'Cornell-Lossless-JPEG', 'deprecated': False},
    'cpal-1.0': {'id': 'CPAL-1.0', 'deprecated': False},
    'cpl-1.0': {'id': 'CPL-1.0', 'deprecated': False},
    'cpol-1.02': {'id': 'CPOL-1.02', 'deprecated': False},
    'cronyx': {'id': 'Cronyx', 'deprecated': False},
    'crossword': {'id': 'Crossword', 'deprecated': False},
    'crystalstacker': {'id': 'CrystalStacker', 'deprecated': False},
    'cua-opl-1.0': {'id': 'CUA-OPL-1.0', 'deprecated': False},
    'cube': {'id': 'Cube', 'deprecated': False},
    'curl': {'id': 'curl', 'deprecated': False},
    'cve-tou': {'id': 'cve-tou', 'deprecated': False},
    'd-fsl-1.0': {'id': 'D-FSL-1.0', 'deprecated': False},
    'dec-3-clause': {'id': 'DEC-3-Clause', 'deprecated': False},
    'diffmark': {'id': 'diffmark', 'deprecated': False},
    'dl-de-by-2.0': {'id': 'DL-DE-BY-2.0', 'deprecated': False},
    'dl-de-zero-2.0': {'id': 'DL-DE-ZERO-2.0', 'deprecated': False},
    'doc': {'id': 'DOC', 'deprecated': False},
    'docbook-schema': {'id': 'DocBook-Schema', 'deprecated': False},
    'docbook-xml': {'id': 'DocBook-XML', 'deprecated': False},
    'dotseqn': {'id': 'Dotseqn', 'deprecated': False},
    'drl-1.0': {'id': 'DRL-1.0', 'deprecated': False},
    'drl-1.1': {'id': 'DRL-1.1', 'deprecated': False},
    'dsdp': {'id': 'DSDP', 'deprecated': False},
    'dtoa': {'id': 'dtoa', 'deprecated': False},
    'dvipdfm': {'id': 'dvipdfm', 'deprecated': False},
    'ecl-1.0': {'id': 'ECL-1.0', 'deprecated': False},
    'ecl-2.0': {'id': 'ECL-2.0', 'deprecated': False},
    'ecos-2.0': {'id': 'eCos-2.0', 'deprecated': True},
    'efl-1.0': {'id': 'EFL-1.0', 'deprecated': False},
    'efl-2.0': {'id': 'EFL-2.0', 'deprecated': False},
    'egenix': {'id': 'eGenix', 'deprecated': False},
    'elastic-2.0': {'id': 'Elastic-2.0', 'deprecated': False},
    'entessa': {'id': 'Entessa', 'deprecated': False},
    'epics': {'id': 'EPICS', 'deprecated': False},
    'epl-1.0': {'id': 'EPL-1.0', 'deprecated': False},
    'epl-2.0': {'id': 'EPL-2.0', 'deprecated': False},
    'erlpl-1.1': {'id': 'ErlPL-1.1', 'deprecated': False},
    'etalab-2.0': {'id': 'etalab-2.0', 'deprecated': False},
    'eudatagrid': {'id': 'EUDatagrid', 'deprecated': False},
    'eupl-1.0': {'id': 'EUPL-1.0', 'deprecated': False},
    'eupl-1.1': {'id': 'EUPL-1.1', 'deprecated': False},
    'eupl-1.2': {'id': 'EUPL-1.2', 'deprecated': False},
    'eurosym': {'id': 'Eurosym', 'deprecated': False},
    'fair': {'id': 'Fair', 'deprecated': False},
    'fbm': {'id': 'FBM', 'deprecated': False},
    'fdk-aac': {'id': 'FDK-AAC', 'deprecated': False},
    'ferguson-twofish': {'id': 'Ferguson-Twofish', 'deprecated': False},
    'frameworx-1.0': {'id': 'Frameworx-1.0', 'deprecated': False},
    'freebsd-doc': {'id': 'FreeBSD-DOC', 'deprecated': False},
    'freeimage': {'id': 'FreeImage', 'deprecated': False},
    'fsfap': {'id': 'FSFAP', 'deprecated': False},
    'fsfap-no-warranty-disclaimer': {'id': 'FSFAP-no-warranty-disclaimer', 'deprecated': False},
    'fsful': {'id': 'FSFUL', 'deprecated': False},
    'fsfullr': {'id': 'FSFULLR', 'deprecated': False},
    'fsfullrwd': {'id': 'FSFULLRWD', 'deprecated': False},
    'ftl': {'id': 'FTL', 'deprecated': False},
    'furuseth': {'id': 'Furuseth', 'deprecated': False},
    'fwlw': {'id': 'fwlw', 'deprecated': False},
    'gcr-docs': {'id': 'GCR-docs', 'deprecated': False},
    'gd': {'id': 'GD', 'deprecated': False},
    'gfdl-1.1': {'id': 'GFDL-1.1', 'deprecated': True},
    'gfdl-1.1-invariants-only': {'id': 'GFDL-1.1-invariants-only', 'deprecated': False},
    'gfdl-1.1-invariants-or-later': {'id': 'GFDL-1.1-invariants-or-later', 'deprecated': False},
    'gfdl-1.1-no-invariants-only': {'id': 'GFDL-1.1-no-invariants-only', 'deprecated': False},
    'gfdl-1.1-no-invariants-or-later': {'id': 'GFDL-1.1-no-invariants-or-later', 'deprecated': False},
    'gfdl-1.1-only': {'id': 'GFDL-1.1-only', 'deprecated': False},
    'gfdl-1.1-or-later': {'id': 'GFDL-1.1-or-later', 'deprecated': False},
    'gfdl-1.2': {'id': 'GFDL-1.2', 'deprecated': True},
    'gfdl-1.2-invariants-only': {'id': 'GFDL-1.2-invariants-only', 'deprecated': False},
    'gfdl-1.2-invariants-or-later': {'id': 'GFDL-1.2-invariants-or-later', 'deprecated': False},
    'gfdl-1.2-no-invariants-only': {'id': 'GFDL-1.2-no-invariants-only', 'deprecated': False},
    'gfdl-1.2-no-invariants-or-later': {'id': 'GFDL-1.2-no-invariants-or-later', 'deprecated': False},
    'gfdl-1.2-only': {'id': 'GFDL-1.2-only', 'deprecated': False},
    'gfdl-1.2-or-later': {'id': 'GFDL-1.2-or-later', 'deprecated': False},
    'gfdl-1.3': {'id': 'GFDL-1.3', 'deprecated': True},
    'gfdl-1.3-invariants-only': {'id': 'GFDL-1.3-invariants-only', 'deprecated': False},
    'gfdl-1.3-invariants-or-later': {'id': 'GFDL-1.3-invariants-or-later', 'deprecated': False},
    'gfdl-1.3-no-invariants-only': {'id': 'GFDL-1.3-no-invariants-only', 'deprecated': False},
    'gfdl-1.3-no-invariants-or-later': {'id': 'GFDL-1.3-no-invariants-or-later', 'deprecated': False},
    'gfdl-1.3-only': {'id': 'GFDL-1.3-only', 'deprecated': False},
    'gfdl-1.3-or-later': {'id': 'GFDL-1.3-or-later', 'deprecated': False},
    'giftware': {'id': 'Giftware', 'deprecated': False},
    'gl2ps': {'id': 'GL2PS', 'deprecated': False},
    'glide': {'id': 'Glide', 'deprecated': False},
    'glulxe': {'id': 'Glulxe', 'deprecated': False},
    'glwtpl': {'id': 'GLWTPL', 'deprecated': False},
    'gnuplot': {'id': 'gnuplot', 'deprecated': False},
    'gpl-1.0': {'id': 'GPL-1.0', 'deprecated': True},
    'gpl-1.0+': {'id': 'GPL-1.0+', 'deprecated': True},
    'gpl-1.0-only': {'id': 'GPL-1.0-only', 'deprecated': False},
    'gpl-1.0-or-later': {'id': 'GPL-1.0-or-later', 'deprecated': False},
    'gpl-2.0': {'id': 'GPL-2.0', 'deprecated': True},
    'gpl-2.0+': {'id': 'GPL-2.0+', 'deprecated': True},
    'gpl-2.0-only': {'id': 'GPL-2.0-only', 'deprecated': False},
    'gpl-2.0-or-later': {'id': 'GPL-2.0-or-later', 'deprecated': False},
    'gpl-2.0-with-autoconf-exception': {'id': 'GPL-2.0-with-autoconf-exception', 'deprecated': True},
    'gpl-2.0-with-bison-exception': {'id': 'GPL-2.0-with-bison-exception', 'deprecated': True},
    'gpl-2.0-with-classpath-exception': {'id': 'GPL-2.0-with-classpath-exception', 'deprecated': True},
    'gpl-2.0-with-font-exception': {'id': 'GPL-2.0-with-font-exception', 'deprecated': True},
    'gpl-2.0-with-gcc-exception': {'id': 'GPL-2.0-with-GCC-exception', 'deprecated': True},
    'gpl-3.0': {'id': 'GPL-3.0', 'deprecated': True},
    'gpl-3.0+': {'id': 'GPL-3.0+', 'deprecated': True},
    'gpl-3.0-only': {'id': 'GPL-3.0-only', 'deprecated': False},
    'gpl-3.0-or-later': {'id': 'GPL-3.0-or-later', 'deprecated': False},
    'gpl-3.0-with-autoconf-exception': {'id': 'GPL-3.0-with-autoconf-exception', 'deprecated': True},
    'gpl-3.0-with-gcc-exception': {'id': 'GPL-3.0-with-GCC-exception', 'deprecated': True},
    'graphics-gems': {'id': 'Graphics-Gems', 'deprecated': False},
    'gsoap-1.3b': {'id': 'gSOAP-1.3b', 'deprecated': False},
    'gtkbook': {'id': 'gtkbook', 'deprecated': False},
    'gutmann': {'id': 'Gutmann', 'deprecated': False},
    'haskellreport': {'id': 'HaskellReport', 'deprecated': False},
    'hdparm': {'id': 'hdparm', 'deprecated': False},
    'hidapi': {'id': 'HIDAPI', 'deprecated': False},
    'hippocratic-2.1': {'id': 'Hippocratic-2.1', 'deprecated': False},
    'hp-1986': {'id': 'HP-1986', 'deprecated': False},
    'hp-1989': {'id': 'HP-1989', 'deprecated': False},
    'hpnd': {'id': 'HPND', 'deprecated': False},
    'hpnd-dec': {'id': 'HPND-DEC', 'deprecated': False},
    'hpnd-doc': {'id': 'HPND-doc', 'deprecated': False},
    'hpnd-doc-sell': {'id': 'HPND-doc-sell', 'deprecated': False},
    'hpnd-export-us': {'id': 'HPND-export-US', 'deprecated': False},
    'hpnd-export-us-acknowledgement': {'id': 'HPND-export-US-acknowledgement', 'deprecated': False},
    'hpnd-export-us-modify': {'id': 'HPND-export-US-modify', 'deprecated': False},
    'hpnd-export2-us': {'id': 'HPND-export2-US', 'deprecated': False},
    'hpnd-fenneberg-livingston': {'id': 'HPND-Fenneberg-Livingston', 'deprecated': False},
    'hpnd-inria-imag': {'id': 'HPND-INRIA-IMAG', 'deprecated': False},
    'hpnd-intel': {'id': 'HPND-Intel', 'deprecated': False},
    'hpnd-kevlin-henney': {'id': 'HPND-Kevlin-Henney', 'deprecated': False},
    'hpnd-markus-kuhn': {'id': 'HPND-Markus-Kuhn', 'deprecated': False},
    'hpnd-merchantability-variant': {'id': 'HPND-merchantability-variant', 'deprecated': False},
    'hpnd-mit-disclaimer': {'id': 'HPND-MIT-disclaimer', 'deprecated': False},
    'hpnd-netrek': {'id': 'HPND-Netrek', 'deprecated': False},
    'hpnd-pbmplus': {'id': 'HPND-Pbmplus', 'deprecated': False},
    'hpnd-sell-mit-disclaimer-xserver': {'id': 'HPND-sell-MIT-disclaimer-xserver', 'deprecated': False},
    'hpnd-sell-regexpr': {'id': 'HPND-sell-regexpr', 'deprecated': False},
    'hpnd-sell-variant': {'id': 'HPND-sell-variant', 'deprecated': False},
    'hpnd-sell-variant-mit-disclaimer': {'id': 'HPND-sell-variant-MIT-disclaimer', 'deprecated': False},
    'hpnd-sell-variant-mit-disclaimer-rev': {'id': 'HPND-sell-variant-MIT-disclaimer-rev', 'deprecated': False},
    'hpnd-uc': {'id': 'HPND-UC', 'deprecated': False},
    'hpnd-uc-export-us': {'id': 'HPND-UC-export-US', 'deprecated': False},
    'htmltidy': {'id': 'HTMLTIDY', 'deprecated': False},
    'ibm-pibs': {'id': 'IBM-pibs', 'deprecated': False},
    'icu': {'id': 'ICU', 'deprecated': False},
    'iec-code-components-eula': {'id': 'IEC-Code-Components-EULA', 'deprecated': False},
    'ijg': {'id': 'IJG', 'deprecated': False},
    'ijg-short': {'id': 'IJG-short', 'deprecated': False},
    'imagemagick': {'id': 'ImageMagick', 'deprecated': False},
    'imatix': {'id': 'iMatix', 'deprecated': False},
    'imlib2': {'id': 'Imlib2', 'deprecated': False},
    'info-zip': {'id': 'Info-ZIP', 'deprecated': False},
    'inner-net-2.0': {'id': 'Inner-Net-2.0', 'deprecated': False},
    'intel': {'id': 'Intel', 'deprecated': False},
    'intel-acpi': {'id': 'Intel-ACPI', 'deprecated': False},
    'interbase-1.0': {'id': 'Interbase-1.0', 'deprecated': False},
    'ipa': {'id': 'IPA', 'deprecated': False},
    'ipl-1.0': {'id': 'IPL-1.0', 'deprecated': False},
    'isc': {'id': 'ISC', 'deprecated': False},
    'isc-veillard': {'id': 'ISC-Veillard', 'deprecated': False},
    'jam': {'id': 'Jam', 'deprecated': False},
    'jasper-2.0': {'id': 'JasPer-2.0', 'deprecated': False},
    'jpl-image': {'id': 'JPL-image', 'deprecated': False},
    'jpnic': {'id': 'JPNIC', 'deprecated': False},
    'json': {'id': 'JSON', 'deprecated': False},
    'kastrup': {'id': 'Kastrup', 'deprecated': False},
    'kazlib': {'id': 'Kazlib', 'deprecated': False},
    'knuth-ctan': {'id': 'Knuth-CTAN', 'deprecated': False},
    'lal-1.2': {'id': 'LAL-1.2', 'deprecated': False},
    'lal-1.3': {'id': 'LAL-1.3', 'deprecated': False},
    'latex2e': {'id': 'Latex2e', 'deprecated': False},
    'latex2e-translated-notice': {'id': 'Latex2e-translated-notice', 'deprecated': False},
    'leptonica': {'id': 'Leptonica', 'deprecated': False},
    'lgpl-2.0': {'id': 'LGPL-2.0', 'deprecated': True},
    'lgpl-2.0+': {'id': 'LGPL-2.0+', 'deprecated': True},
    'lgpl-2.0-only': {'id': 'LGPL-2.0-only', 'deprecated': False},
    'lgpl-2.0-or-later': {'id': 'LGPL-2.0-or-later', 'deprecated': False},
    'lgpl-2.1': {'id': 'LGPL-2.1', 'deprecated': True},
    'lgpl-2.1+': {'id': 'LGPL-2.1+', 'deprecated': True},
    'lgpl-2.1-only': {'id': 'LGPL-2.1-only', 'deprecated': False},
    'lgpl-2.1-or-later': {'id': 'LGPL-2.1-or-later', 'deprecated': False},
    'lgpl-3.0': {'id': 'LGPL-3.0', 'deprecated': True},
    'lgpl-3.0+': {'id': 'LGPL-3.0+', 'deprecated': True},
    'lgpl-3.0-only': {'id': 'LGPL-3.0-only', 'deprecated': False},
    'lgpl-3.0-or-later': {'id': 'LGPL-3.0-or-later', 'deprecated': False},
    'lgpllr': {'id': 'LGPLLR', 'deprecated': False},
    'libpng': {'id': 'Libpng', 'deprecated': False},
    'libpng-2.0': {'id': 'libpng-2.0', 'deprecated': False},
    'libselinux-1.0': {'id': 'libselinux-1.0', 'deprecated': False},
    'libtiff': {'id': 'libtiff', 'deprecated': False},
    'libutil-david-nugent': {'id': 'libutil-David-Nugent', 'deprecated': False},
    'liliq-p-1.1': {'id': 'LiLiQ-P-1.1', 'deprecated': False},
    'liliq-r-1.1': {'id': 'LiLiQ-R-1.1', 'deprecated': False},
    'liliq-rplus-1.1': {'id': 'LiLiQ-Rplus-1.1', 'deprecated': False},
    'linux-man-pages-1-para': {'id': 'Linux-man-pages-1-para', 'deprecated': False},
    'linux-man-pages-copyleft': {'id': 'Linux-man-pages-copyleft', 'deprecated': False},
    'linux-man-pages-copyleft-2-para': {'id': 'Linux-man-pages-copyleft-2-para', 'deprecated': False},
    'linux-man-pages-copyleft-var': {'id': 'Linux-man-pages-copyleft-var', 'deprecated': False},
    'linux-openib': {'id': 'Linux-OpenIB', 'deprecated': False},
    'loop': {'id': 'LOOP', 'deprecated': False},
    'lpd-document': {'id': 'LPD-document', 'deprecated': False},
    'lpl-1.0': {'id': 'LPL-1.0', 'deprecated': False},
    'lpl-1.02': {'id': 'LPL-1.02', 'deprecated': False},
    'lppl-1.0': {'id': 'LPPL-1.0', 'deprecated': False},
    'lppl-1.1': {'id': 'LPPL-1.1', 'deprecated': False},
    'lppl-1.2': {'id': 'LPPL-1.2', 'deprecated': False},
    'lppl-1.3a': {'id': 'LPPL-1.3a', 'deprecated': False},
    'lppl-1.3c': {'id': 'LPPL-1.3c', 'deprecated': False},
    'lsof': {'id': 'lsof', 'deprecated': False},
    'lucida-bitmap-fonts': {'id': 'Lucida-Bitmap-Fonts', 'deprecated': False},
    'lzma-sdk-9.11-to-9.20': {'id': 'LZMA-SDK-9.11-to-9.20', 'deprecated': False},
    'lzma-sdk-9.22': {'id': 'LZMA-SDK-9.22', 'deprecated': False},
    'mackerras-3-clause': {'id': 'Mackerras-3-Clause', 'deprecated': False},
    'mackerras-3-clause-acknowledgment': {'id': 'Mackerras-3-Clause-acknowledgment', 'deprecated': False},
    'magaz': {'id': 'magaz', 'deprecated': False},
    'mailprio': {'id': 'mailprio', 'deprecated': False},
    'makeindex': {'id': 'MakeIndex', 'deprecated': False},
    'martin-birgmeier': {'id': 'Martin-Birgmeier', 'deprecated': False},
    'mcphee-slideshow': {'id': 'McPhee-slideshow', 'deprecated': False},
    'metamail': {'id': 'metamail', 'deprecated': False},
    'minpack': {'id': 'Minpack', 'deprecated': False},
    'miros': {'id': 'MirOS', 'deprecated': False},
    'mit': {'id': 'MIT', 'deprecated': False},
    'mit-0': {'id': 'MIT-0', 'deprecated': False},
    'mit-advertising': {'id': 'MIT-advertising', 'deprecated': False},
    'mit-cmu': {'id': 'MIT-CMU', 'deprecated': False},
    'mit-enna': {'id': 'MIT-enna', 'deprecated': False},
    'mit-feh': {'id': 'MIT-feh', 'deprecated': False},
    'mit-festival': {'id': 'MIT-Festival', 'deprecated': False},
    'mit-khronos-old': {'id': 'MIT-Khronos-old', 'deprecated': False},
    'mit-modern-variant': {'id': 'MIT-Modern-Variant', 'deprecated': False},
    'mit-open-group': {'id': 'MIT-open-group', 'deprecated': False},
    'mit-testregex': {'id': 'MIT-testregex', 'deprecated': False},
    'mit-wu': {'id': 'MIT-Wu', 'deprecated': False},
    'mitnfa': {'id': 'MITNFA', 'deprecated': False},
    'mmixware': {'id': 'MMIXware', 'deprecated': False},
    'motosoto': {'id': 'Motosoto', 'deprecated': False},
    'mpeg-ssg': {'id': 'MPEG-SSG', 'deprecated': False},
    'mpi-permissive': {'id': 'mpi-permissive', 'deprecated': False},
    'mpich2': {'id': 'mpich2', 'deprecated': False},
    'mpl-1.0': {'id': 'MPL-1.0', 'deprecated': False},
    'mpl-1.1': {'id': 'MPL-1.1', 'deprecated': False},
    'mpl-2.0': {'id': 'MPL-2.0', 'deprecated': False},
    'mpl-2.0-no-copyleft-exception': {'id': 'MPL-2.0-no-copyleft-exception', 'deprecated': False},
    'mplus': {'id': 'mplus', 'deprecated': False},
    'ms-lpl': {'id': 'MS-LPL', 'deprecated': False},
    'ms-pl': {'id': 'MS-PL', 'deprecated': False},
    'ms-rl': {'id': 'MS-RL', 'deprecated': False},
    'mtll': {'id': 'MTLL', 'deprecated': False},
    'mulanpsl-1.0': {'id': 'MulanPSL-1.0', 'deprecated': False},
    'mulanpsl-2.0': {'id': 'MulanPSL-2.0', 'deprecated': False},
    'multics': {'id': 'Multics', 'deprecated': False},
    'mup': {'id': 'Mup', 'deprecated': False},
    'naist-2003': {'id': 'NAIST-2003', 'deprecated': False},
    'nasa-1.3': {'id': 'NASA-1.3', 'deprecated': False},
    'naumen': {'id': 'Naumen', 'deprecated': False},
    'nbpl-1.0': {'id': 'NBPL-1.0', 'deprecated': False},
    'ncbi-pd': {'id': 'NCBI-PD', 'deprecated': False},
    'ncgl-uk-2.0': {'id': 'NCGL-UK-2.0', 'deprecated': False},
    'ncl': {'id': 'NCL', 'deprecated': False},
    'ncsa': {'id': 'NCSA', 'deprecated': False},
    'net-snmp': {'id': 'Net-SNMP', 'deprecated': True},
    'netcdf': {'id': 'NetCDF', 'deprecated': False},
    'newsletr': {'id': 'Newsletr', 'deprecated': False},
    'ngpl': {'id': 'NGPL', 'deprecated': False},
    'nicta-1.0': {'id': 'NICTA-1.0', 'deprecated': False},
    'nist-pd': {'id': 'NIST-PD', 'deprecated': False},
    'nist-pd-fallback': {'id': 'NIST-PD-fallback', 'deprecated': False},
    'nist-software': {'id': 'NIST-Software', 'deprecated': False},
    'nlod-1.0': {'id': 'NLOD-1.0', 'deprecated': False},
    'nlod-2.0': {'id': 'NLOD-2.0', 'deprecated': False},
    'nlpl': {'id': 'NLPL', 'deprecated': False},
    'nokia': {'id': 'Nokia', 'deprecated': False},
    'nosl': {'id': 'NOSL', 'deprecated': False},
    'noweb': {'id': 'Noweb', 'deprecated': False},
    'npl-1.0': {'id': 'NPL-1.0', 'deprecated': False},
    'npl-1.1': {'id': 'NPL-1.1', 'deprecated': False},
    'nposl-3.0': {'id': 'NPOSL-3.0', 'deprecated': False},
    'nrl': {'id': 'NRL', 'deprecated': False},
    'ntp': {'id': 'NTP', 'deprecated': False},
    'ntp-0': {'id': 'NTP-0', 'deprecated': False},
    'nunit': {'id': 'Nunit', 'deprecated': True},
    'o-uda-1.0': {'id': 'O-UDA-1.0', 'deprecated': False},
    'oar': {'id': 'OAR', 'deprecated': False},
    'occt-pl': {'id': 'OCCT-PL', 'deprecated': False},
    'oclc-2.0': {'id': 'OCLC-2.0', 'deprecated': False},
    'odbl-1.0': {'id': 'ODbL-1.0', 'deprecated': False},
    'odc-by-1.0': {'id': 'ODC-By-1.0', 'deprecated': False},
    'offis': {'id': 'OFFIS', 'deprecated': False},
    'ofl-1.0': {'id': 'OFL-1.0', 'deprecated': False},
    'ofl-1.0-no-rfn': {'id': 'OFL-1.0-no-RFN', 'deprecated': False},
    'ofl-1.0-rfn': {'id': 'OFL-1.0-RFN', 'deprecated': False},
    'ofl-1.1': {'id': 'OFL-1.1', 'deprecated': False},
    'ofl-1.1-no-rfn': {'id': 'OFL-1.1-no-RFN', 'deprecated': False},
    'ofl-1.1-rfn': {'id': 'OFL-1.1-RFN', 'deprecated': False},
    'ogc-1.0': {'id': 'OGC-1.0', 'deprecated': False},
    'ogdl-taiwan-1.0': {'id': 'OGDL-Taiwan-1.0', 'deprecated': False},
    'ogl-canada-2.0': {'id': 'OGL-Canada-2.0', 'deprecated': False},
    'ogl-uk-1.0': {'id': 'OGL-UK-1.0', 'deprecated': False},
    'ogl-uk-2.0': {'id': 'OGL-UK-2.0', 'deprecated': False},
    'ogl-uk-3.0': {'id': 'OGL-UK-3.0', 'deprecated': False},
    'ogtsl': {'id': 'OGTSL', 'deprecated': False},
    'oldap-1.1': {'id': 'OLDAP-1.1', 'deprecated': False},
    'oldap-1.2': {'id': 'OLDAP-1.2', 'deprecated': False},
    'oldap-1.3': {'id': 'OLDAP-1.3', 'deprecated': False},
    'oldap-1.4': {'id': 'OLDAP-1.4', 'deprecated': False},
    'oldap-2.0': {'id': 'OLDAP-2.0', 'deprecated': False},
    'oldap-2.0.1': {'id': 'OLDAP-2.0.1', 'deprecated': False},
    'oldap-2.1': {'id': 'OLDAP-2.1', 'deprecated': False},
    'oldap-2.2': {'id': 'OLDAP-2.2', 'deprecated': False},
    'oldap-2.2.1': {'id': 'OLDAP-2.2.1', 'deprecated': False},
    'oldap-2.2.2': {'id': 'OLDAP-2.2.2', 'deprecated': False},
    'oldap-2.3': {'id': 'OLDAP-2.3', 'deprecated': False},
    'oldap-2.4': {'id': 'OLDAP-2.4', 'deprecated': False},
    'oldap-2.5': {'id': 'OLDAP-2.5', 'deprecated': False},
    'oldap-2.6': {'id': 'OLDAP-2.6', 'deprecated': False},
    'oldap-2.7': {'id': 'OLDAP-2.7', 'deprecated': False},
    'oldap-2.8': {'id': 'OLDAP-2.8', 'deprecated': False},
    'olfl-1.3': {'id': 'OLFL-1.3', 'deprecated': False},
    'oml': {'id': 'OML', 'deprecated': False},
    'openpbs-2.3': {'id': 'OpenPBS-2.3', 'deprecated': False},
    'openssl': {'id': 'OpenSSL', 'deprecated': False},
    'openssl-standalone': {'id': 'OpenSSL-standalone', 'deprecated': False},
    'openvision': {'id': 'OpenVision', 'deprecated': False},
    'opl-1.0': {'id': 'OPL-1.0', 'deprecated': False},
    'opl-uk-3.0': {'id': 'OPL-UK-3.0', 'deprecated': False},
    'opubl-1.0': {'id': 'OPUBL-1.0', 'deprecated': False},
    'oset-pl-2.1': {'id': 'OSET-PL-2.1', 'deprecated': False},
    'osl-1.0': {'id': 'OSL-1.0', 'deprecated': False},
    'osl-1.1': {'id': 'OSL-1.1', 'deprecated': False},
    'osl-2.0': {'id': 'OSL-2.0', 'deprecated': False},
    'osl-2.1': {'id': 'OSL-2.1', 'deprecated': False},
    'osl-3.0': {'id': 'OSL-3.0', 'deprecated': False},
    'padl': {'id': 'PADL', 'deprecated': False},
    'parity-6.0.0': {'id': 'Parity-6.0.0', 'deprecated': False},
    'parity-7.0.0': {'id': 'Parity-7.0.0', 'deprecated': False},
    'pddl-1.0': {'id': 'PDDL-1.0', 'deprecated': False},
    'php-3.0': {'id': 'PHP-3.0', 'deprecated': False},
    'php-3.01': {'id': 'PHP-3.01', 'deprecated': False},
    'pixar': {'id': 'Pixar', 'deprecated': False},
    'pkgconf': {'id': 'pkgconf', 'deprecated': False},
    'plexus': {'id': 'Plexus', 'deprecated': False},
    'pnmstitch': {'id': 'pnmstitch', 'deprecated': False},
    'polyform-noncommercial-1.0.0': {'id': 'PolyForm-Noncommercial-1.0.0', 'deprecated': False},
    'polyform-small-business-1.0.0': {'id': 'PolyForm-Small-Business-1.0.0', 'deprecated': False},
    'postgresql': {'id': 'PostgreSQL', 'deprecated': False},
    'ppl': {'id': 'PPL', 'deprecated': False},
    'psf-2.0': {'id': 'PSF-2.0', 'deprecated': False},
    'psfrag': {'id': 'psfrag', 'deprecated': False},
    'psutils': {'id': 'psutils', 'deprecated': False},
    'python-2.0': {'id': 'Python-2.0', 'deprecated': False},
    'python-2.0.1': {'id': 'Python-2.0.1', 'deprecated': False},
    'python-ldap': {'id': 'python-ldap', 'deprecated': False},
    'qhull': {'id': 'Qhull', 'deprecated': False},
    'qpl-1.0': {'id': 'QPL-1.0', 'deprecated': False},
    'qpl-1.0-inria-2004': {'id': 'QPL-1.0-INRIA-2004', 'deprecated': False},
    'radvd': {'id': 'radvd', 'deprecated': False},
    'rdisc': {'id': 'Rdisc', 'deprecated': False},
    'rhecos-1.1': {'id': 'RHeCos-1.1', 'deprecated': False},
    'rpl-1.1': {'id': 'RPL-1.1', 'deprecated': False},
    'rpl-1.5': {'id': 'RPL-1.5', 'deprecated': False},
    'rpsl-1.0': {'id': 'RPSL-1.0', 'deprecated': False},
    'rsa-md': {'id': 'RSA-MD', 'deprecated': False},
    'rscpl': {'id': 'RSCPL', 'deprecated': False},
    'ruby': {'id': 'Ruby', 'deprecated': False},
    'ruby-pty': {'id': 'Ruby-pty', 'deprecated': False},
    'sax-pd': {'id': 'SAX-PD', 'deprecated': False},
    'sax-pd-2.0': {'id': 'SAX-PD-2.0', 'deprecated': False},
    'saxpath': {'id': 'Saxpath', 'deprecated': False},
    'scea': {'id': 'SCEA', 'deprecated': False},
    'schemereport': {'id': 'SchemeReport', 'deprecated': False},
    'sendmail': {'id': 'Sendmail', 'deprecated': False},
    'sendmail-8.23': {'id': 'Sendmail-8.23', 'deprecated': False},
    'sgi-b-1.0': {'id': 'SGI-B-1.0', 'deprecated': False},
    'sgi-b-1.1': {'id': 'SGI-B-1.1', 'deprecated': False},
    'sgi-b-2.0': {'id': 'SGI-B-2.0', 'deprecated': False},
    'sgi-opengl': {'id': 'SGI-OpenGL', 'deprecated': False},
    'sgp4': {'id': 'SGP4', 'deprecated': False},
    'shl-0.5': {'id': 'SHL-0.5', 'deprecated': False},
    'shl-0.51': {'id': 'SHL-0.51', 'deprecated': False},
    'simpl-2.0': {'id': 'SimPL-2.0', 'deprecated': False},
    'sissl': {'id': 'SISSL', 'deprecated': False},
    'sissl-1.2': {'id': 'SISSL-1.2', 'deprecated': False},
    'sl': {'id': 'SL', 'deprecated': False},
    'sleepycat': {'id': 'Sleepycat', 'deprecated': False},
    'smlnj': {'id': 'SMLNJ', 'deprecated': False},
    'smppl': {'id': 'SMPPL', 'deprecated': False},
    'snia': {'id': 'SNIA', 'deprecated': False},
    'snprintf': {'id': 'snprintf', 'deprecated': False},
    'softsurfer': {'id': 'softSurfer', 'deprecated': False},
    'soundex': {'id': 'Soundex', 'deprecated': False},
    'spencer-86': {'id': 'Spencer-86', 'deprecated': False},
    'spencer-94': {'id': 'Spencer-94', 'deprecated': False},
    'spencer-99': {'id': 'Spencer-99', 'deprecated': False},
    'spl-1.0': {'id': 'SPL-1.0', 'deprecated': False},
    'ssh-keyscan': {'id': 'ssh-keyscan', 'deprecated': False},
    'ssh-openssh': {'id': 'SSH-OpenSSH', 'deprecated': False},
    'ssh-short': {'id': 'SSH-short', 'deprecated': False},
    'ssleay-standalone': {'id': 'SSLeay-standalone', 'deprecated': False},
    'sspl-1.0': {'id': 'SSPL-1.0', 'deprecated': False},
    'standardml-nj': {'id': 'StandardML-NJ', 'deprecated': True},
    'sugarcrm-1.1.3': {'id': 'SugarCRM-1.1.3', 'deprecated': False},
    'sun-ppp': {'id': 'Sun-PPP', 'deprecated': False},
    'sun-ppp-2000': {'id': 'Sun-PPP-2000', 'deprecated': False},
    'sunpro': {'id': 'SunPro', 'deprecated': False},
    'swl': {'id': 'SWL', 'deprecated': False},
    'swrule': {'id': 'swrule', 'deprecated': False},
    'symlinks': {'id': 'Symlinks', 'deprecated': False},
    'tapr-ohl-1.0': {'id': 'TAPR-OHL-1.0', 'deprecated': False},
    'tcl': {'id': 'TCL', 'deprecated': False},
    'tcp-wrappers': {'id': 'TCP-wrappers', 'deprecated': False},
    'termreadkey': {'id': 'TermReadKey', 'deprecated': False},
    'tgppl-1.0': {'id': 'TGPPL-1.0', 'deprecated': False},
    'threeparttable': {'id': 'threeparttable', 'deprecated': False},
    'tmate': {'id': 'TMate', 'deprecated': False},
    'torque-1.1': {'id': 'TORQUE-1.1', 'deprecated': False},
    'tosl': {'id': 'TOSL', 'deprecated': False},
    'tpdl': {'id': 'TPDL', 'deprecated': False},
    'tpl-1.0': {'id': 'TPL-1.0', 'deprecated': False},
    'ttwl': {'id': 'TTWL', 'deprecated': False},
    'ttyp0': {'id': 'TTYP0', 'deprecated': False},
    'tu-berlin-1.0': {'id': 'TU-Berlin-1.0', 'deprecated': False},
    'tu-berlin-2.0': {'id': 'TU-Berlin-2.0', 'deprecated': False},
    'ubuntu-font-1.0': {'id': 'Ubuntu-font-1.0', 'deprecated': False},
    'ucar': {'id': 'UCAR', 'deprecated': False},
    'ucl-1.0': {'id': 'UCL-1.0', 'deprecated': False},
    'ulem': {'id': 'ulem', 'deprecated': False},
    'umich-merit': {'id': 'UMich-Merit', 'deprecated': False},
    'unicode-3.0': {'id': 'Unicode-3.0', 'deprecated': False},
    'unicode-dfs-2015': {'id': 'Unicode-DFS-2015', 'deprecated': False},
    'unicode-dfs-2016': {'id': 'Unicode-DFS-2016', 'deprecated': False},
    'unicode-tou': {'id': 'Unicode-TOU', 'deprecated': False},
    'unixcrypt': {'id': 'UnixCrypt', 'deprecated': False},
    'unlicense': {'id': 'Unlicense', 'deprecated': False},
    'upl-1.0': {'id': 'UPL-1.0', 'deprecated': False},
    'urt-rle': {'id': 'URT-RLE', 'deprecated': False},
    'vim': {'id': 'Vim', 'deprecated': False},
    'vostrom': {'id': 'VOSTROM', 'deprecated': False},
    'vsl-1.0': {'id': 'VSL-1.0', 'deprecated': False},
    'w3c': {'id': 'W3C', 'deprecated': False},
    'w3c-19980720': {'id': 'W3C-19980720', 'deprecated': False},
    'w3c-20150513': {'id': 'W3C-20150513', 'deprecated': False},
    'w3m': {'id': 'w3m', 'deprecated': False},
    'watcom-1.0': {'id': 'Watcom-1.0', 'deprecated': False},
    'widget-workshop': {'id': 'Widget-Workshop', 'deprecated': False},
    'wsuipa': {'id': 'Wsuipa', 'deprecated': False},
    'wtfpl': {'id': 'WTFPL', 'deprecated': False},
    'wxwindows': {'id': 'wxWindows', 'deprecated': True},
    'x11': {'id': 'X11', 'deprecated': False},
    'x11-distribute-modifications-variant': {'id': 'X11-distribute-modifications-variant', 'deprecated': False},
    'x11-swapped': {'id': 'X11-swapped', 'deprecated': False},
    'xdebug-1.03': {'id': 'Xdebug-1.03', 'deprecated': False},
    'xerox': {'id': 'Xerox', 'deprecated': False},
    'xfig': {'id': 'Xfig', 'deprecated': False},
    'xfree86-1.1': {'id': 'XFree86-1.1', 'deprecated': False},
    'xinetd': {'id': 'xinetd', 'deprecated': False},
    'xkeyboard-config-zinoviev': {'id': 'xkeyboard-config-Zinoviev', 'deprecated': False},
    'xlock': {'id': 'xlock', 'deprecated': False},
    'xnet': {'id': 'Xnet', 'deprecated': False},
    'xpp': {'id': 'xpp', 'deprecated': False},
    'xskat': {'id': 'XSkat', 'deprecated': False},
    'xzoom': {'id': 'xzoom', 'deprecated': False},
    'ypl-1.0': {'id': 'YPL-1.0', 'deprecated': False},
    'ypl-1.1': {'id': 'YPL-1.1', 'deprecated': False},
    'zed': {'id': 'Zed', 'deprecated': False},
    'zeeff': {'id': 'Zeeff', 'deprecated': False},
    'zend-2.0': {'id': 'Zend-2.0', 'deprecated': False},
    'zimbra-1.3': {'id': 'Zimbra-1.3', 'deprecated': False},
    'zimbra-1.4': {'id': 'Zimbra-1.4', 'deprecated': False},
    'zlib': {'id': 'Zlib', 'deprecated': False},
    'zlib-acknowledgement': {'id': 'zlib-acknowledgement', 'deprecated': False},
    'zpl-1.1': {'id': 'ZPL-1.1', 'deprecated': False},
    'zpl-2.0': {'id': 'ZPL-2.0', 'deprecated': False},
    'zpl-2.1': {'id': 'ZPL-2.1', 'deprecated': False},
}

EXCEPTIONS: dict[str, SPDXException] = {
    '389-exception': {'id': '389-exception', 'deprecated': False},
    'asterisk-exception': {'id': 'Asterisk-exception', 'deprecated': False},
    'asterisk-linking-protocols-exception': {'id': 'Asterisk-linking-protocols-exception', 'deprecated': False},
    'autoconf-exception-2.0': {'id': 'Autoconf-exception-2.0', 'deprecated': False},
    'autoconf-exception-3.0': {'id': 'Autoconf-exception-3.0', 'deprecated': False},
    'autoconf-exception-generic': {'id': 'Autoconf-exception-generic', 'deprecated': False},
    'autoconf-exception-generic-3.0': {'id': 'Autoconf-exception-generic-3.0', 'deprecated': False},
    'autoconf-exception-macro': {'id': 'Autoconf-exception-macro', 'deprecated': False},
    'bison-exception-1.24': {'id': 'Bison-exception-1.24', 'deprecated': False},
    'bison-exception-2.2': {'id': 'Bison-exception-2.2', 'deprecated': False},
    'bootloader-exception': {'id': 'Bootloader-exception', 'deprecated': False},
    'classpath-exception-2.0': {'id': 'Classpath-exception-2.0', 'deprecated': False},
    'clisp-exception-2.0': {'id': 'CLISP-exception-2.0', 'deprecated': False},
    'cryptsetup-openssl-exception': {'id': 'cryptsetup-OpenSSL-exception', 'deprecated': False},
    'digirule-foss-exception': {'id': 'DigiRule-FOSS-exception', 'deprecated': False},
    'ecos-exception-2.0': {'id': 'eCos-exception-2.0', 'deprecated': False},
    'erlang-otp-linking-exception': {'id': 'erlang-otp-linking-exception', 'deprecated': False},
    'fawkes-runtime-exception': {'id': 'Fawkes-Runtime-exception', 'deprecated': False},
    'fltk-exception': {'id': 'FLTK-exception', 'deprecated': False},
    'fmt-exception': {'id': 'fmt-exception', 'deprecated': False},
    'font-exception-2.0': {'id': 'Font-exception-2.0', 'deprecated': False},
    'freertos-exception-2.0': {'id': 'freertos-exception-2.0', 'deprecated': False},
    'gcc-exception-2.0': {'id': 'GCC-exception-2.0', 'deprecated': False},
    'gcc-exception-2.0-note': {'id': 'GCC-exception-2.0-note', 'deprecated': False},
    'gcc-exception-3.1': {'id': 'GCC-exception-3.1', 'deprecated': False},
    'gmsh-exception': {'id': 'Gmsh-exception', 'deprecated': False},
    'gnat-exception': {'id': 'GNAT-exception', 'deprecated': False},
    'gnome-examples-exception': {'id': 'GNOME-examples-exception', 'deprecated': False},
    'gnu-compiler-exception': {'id': 'GNU-compiler-exception', 'deprecated': False},
    'gnu-javamail-exception': {'id': 'gnu-javamail-exception', 'deprecated': False},
    'gpl-3.0-interface-exception': {'id': 'GPL-3.0-interface-exception', 'deprecated': False},
    'gpl-3.0-linking-exception': {'id': 'GPL-3.0-linking-exception', 'deprecated': False},
    'gpl-3.0-linking-source-exception': {'id': 'GPL-3.0-linking-source-exception', 'deprecated': False},
    'gpl-cc-1.0': {'id': 'GPL-CC-1.0', 'deprecated': False},
    'gstreamer-exception-2005': {'id': 'GStreamer-exception-2005', 'deprecated': False},
    'gstreamer-exception-2008': {'id': 'GStreamer-exception-2008', 'deprecated': False},
    'i2p-gpl-java-exception': {'id': 'i2p-gpl-java-exception', 'deprecated': False},
    'kicad-libraries-exception': {'id': 'KiCad-libraries-exception', 'deprecated': False},
    'lgpl-3.0-linking-exception': {'id': 'LGPL-3.0-linking-exception', 'deprecated': False},
    'libpri-openh323-exception': {'id': 'libpri-OpenH323-exception', 'deprecated': False},
    'libtool-exception': {'id': 'Libtool-exception', 'deprecated': False},
    'linux-syscall-note': {'id': 'Linux-syscall-note', 'deprecated': False},
    'llgpl': {'id': 'LLGPL', 'deprecated': False},
    'llvm-exception': {'id': 'LLVM-exception', 'deprecated': False},
    'lzma-exception': {'id': 'LZMA-exception', 'deprecated': False},
    'mif-exception': {'id': 'mif-exception', 'deprecated': False},
    'nokia-qt-exception-1.1': {'id': 'Nokia-Qt-exception-1.1', 'deprecated': True},
    'ocaml-lgpl-linking-exception': {'id': 'OCaml-LGPL-linking-exception', 'deprecated': False},
    'occt-exception-1.0': {'id': 'OCCT-exception-1.0', 'deprecated': False},
    'openjdk-assembly-exception-1.0': {'id': 'OpenJDK-assembly-exception-1.0', 'deprecated': False},
    'openvpn-openssl-exception': {'id': 'openvpn-openssl-exception', 'deprecated': False},
    'pcre2-exception': {'id': 'PCRE2-exception', 'deprecated': False},
    'ps-or-pdf-font-exception-20170817': {'id': 'PS-or-PDF-font-exception-20170817', 'deprecated': False},
    'qpl-1.0-inria-2004-exception': {'id': 'QPL-1.0-INRIA-2004-exception', 'deprecated': False},
    'qt-gpl-exception-1.0': {'id': 'Qt-GPL-exception-1.0', 'deprecated': False},
    'qt-lgpl-exception-1.1': {'id': 'Qt-LGPL-exception-1.1', 'deprecated': False},
    'qwt-exception-1.0': {'id': 'Qwt-exception-1.0', 'deprecated': False},
    'romic-exception': {'id': 'romic-exception', 'deprecated': False},
    'rrdtool-floss-exception-2.0': {'id': 'RRDtool-FLOSS-exception-2.0', 'deprecated': False},
    'sane-exception': {'id': 'SANE-exception', 'deprecated': False},
    'shl-2.0': {'id': 'SHL-2.0', 'deprecated': False},
    'shl-2.1': {'id': 'SHL-2.1', 'deprecated': False},
    'stunnel-exception': {'id': 'stunnel-exception', 'deprecated': False},
    'swi-exception': {'id': 'SWI-exception', 'deprecated': False},
    'swift-exception': {'id': 'Swift-exception', 'deprecated': False},
    'texinfo-exception': {'id': 'Texinfo-exception', 'deprecated': False},
    'u-boot-exception-2.0': {'id': 'u-boot-exception-2.0', 'deprecated': False},
    'ubdl-exception': {'id': 'UBDL-exception', 'deprecated': False},
    'universal-foss-exception-1.0': {'id': 'Universal-FOSS-exception-1.0', 'deprecated': False},
    'vsftpd-openssl-exception': {'id': 'vsftpd-openssl-exception', 'deprecated': False},
    'wxwindows-exception-3.1': {'id': 'WxWindows-exception-3.1', 'deprecated': False},
    'x11vnc-openssl-exception': {'id': 'x11vnc-openssl-exception', 'deprecated': False},
}
Copyright (c) 2008-present The pip developers (see AUTHORS.txt file)

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

### License for 3rd party library pytz

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

### License for 3rd party library requests


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


---

### License for 3rd party library urllib3

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


