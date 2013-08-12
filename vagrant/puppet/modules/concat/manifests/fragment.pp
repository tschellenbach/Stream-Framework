# Puts a file fragment into a directory previous setup using concat
#
# OPTIONS:
#   - target    The file that these fragments belong to
#   - content   If present puts the content into the file
#   - source    If content was not specified, use the source
#   - order     By default all files gets a 10_ prefix in the directory
#               you can set it to anything else using this to influence the
#               order of the content in the file
#   - ensure    Present/Absent or destination to a file to include another file
#   - mode      Mode for the file
#   - owner     Owner of the file
#   - group     Owner of the file
#   - backup    Controls the filebucketing behavior of the final file and
#               see File type reference for its use.  Defaults to 'puppet'
define concat::fragment($target, $content='', $source='', $order=10, $ensure = 'present', $mode = '0644', $owner = $::id, $group = $concat::setup::root_group, $backup = 'puppet') {
  $safe_name = regsubst($name, '/', '_', 'G')
  $safe_target_name = regsubst($target, '/', '_', 'G')
  $concatdir = $concat::setup::concatdir
  $fragdir = "${concatdir}/${safe_target_name}"

  # if content is passed, use that, else if source is passed use that
  # if neither passed, but $ensure is in symlink form, make a symlink
  case $content {
    '': {
      case $source {
        '': {
          case $ensure {
            '', 'absent', 'present', 'file', 'directory': {
              crit('No content, source or symlink specified')
            }
            default: {
              #do nothing, make puppet-lint happy.
            }
          }
        }
        default: { File{ source => $source } }
      }
    }
    default: { File{ content => $content } }
  }

  file{"${fragdir}/fragments/${order}_${safe_name}":
    ensure => $ensure,
    mode   => $mode,
    owner  => $owner,
    group  => $group,
    backup => $backup,
    alias  => "concat_fragment_${name}",
    notify => Exec["concat_${target}"]
  }
}
